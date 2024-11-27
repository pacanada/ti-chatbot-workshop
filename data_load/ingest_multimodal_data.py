import base64
import json
import uuid
from pathlib import Path

import redis
from config import Config
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_community.storage import RedisStore
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

config = Config()


def load_serialized_data(
    data_folder: Path,
) -> tuple[dict[str, dict], dict[str, dict], dict[str, list]]:
    """
    Load all serialized data from the output folder structure
    Returns dictionaries of texts, tables, and images organized by file name
    """
    all_texts: dict[str, dict] = {}
    all_tables: dict[str, dict] = {}
    all_images: dict[str, list] = {}

    # Iterate through each subfolder (one per processed file)
    for folder_path in data_folder.iterdir():
        if not folder_path.is_dir():
            continue

        folder_name = folder_path.name

        # Load texts
        text_path = folder_path / "texts.json"
        if text_path.exists():
            with text_path.open(encoding="utf-8") as f:
                all_texts[folder_name] = json.load(f)

        # Load tables
        table_path = folder_path / "tables.json"
        if table_path.exists():
            with table_path.open(encoding="utf-8") as f:
                all_tables[folder_name] = json.load(f)

        # Load images from the images subfolder
        images_folder = folder_path / "images"
        if images_folder.exists():
            all_images[folder_name] = []
            for img_file in images_folder.iterdir():
                if img_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    # Create a tuple of (image_name, base64_string)
                    img_base64 = encode_image(img_file)
                    all_images[folder_name].append((img_file.name, img_base64))

    return all_texts, all_tables, all_images


def encode_image(image_path: Path) -> str:
    """Getting the base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_text_summaries(
    texts_dict: dict[str, list[str]],
    tables_dict: dict[str, list[str]],
    summarize_texts: bool = False,
    model: AzureChatOpenAI = None,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    Summarize text elements organized by file
    texts_dict: Dictionary of texts by file name
    tables_dict: Dictionary of tables by file name
    summarize_texts: Bool to summarize texts
    """
    text_summaries = {}
    table_summaries = {}

    # Prompt
    prompt_text = """You are an assistant tasked with summarizing tables and text for retrieval. \
    These summaries will be embedded and used to retrieve the raw text or table elements. \
    Give a concise summary of the table or text that is well optimized for retrieval.
    Table or text: {element}
    """
    prompt = ChatPromptTemplate.from_template(prompt_text)

    summarize_chain = {"element": lambda x: x} | prompt | model | StrOutputParser()

    # Process texts by file
    for file_name, texts in texts_dict.items():
        if texts and summarize_texts:
            text_summaries[file_name] = summarize_chain.batch(texts, {"max_concurrency": 5})
        elif texts:
            text_summaries[file_name] = texts

    # Process tables by file
    for file_name, tables in tables_dict.items():
        if tables:
            table_summaries[file_name] = summarize_chain.batch(tables, {"max_concurrency": 5})

    return text_summaries, table_summaries


def generate_img_summaries(
    images_dict: dict[str, list[tuple[str, str]]], model: AzureChatOpenAI
) -> dict[str, list[tuple[str, str]]]:
    """
    Generate summaries for images organized by file
    images_dict: Dictionary of (image_name, base64_string) tuples by file name
    """
    image_summaries = {}

    prompt = """You are an assistant tasked with summarizing images for retrieval. \
    These summaries will be embedded and used to retrieve the raw image. \
    Give a concise summary of the image that is well optimized for retrieval. \
    Do not add the Summary: prefix. Just provide the description."""

    for file_name, images in images_dict.items():
        image_summaries[file_name] = []
        for img_name, img_base64 in images:
            msg = model.invoke(
                [
                    HumanMessage(
                        content=[
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                            },
                        ]
                    )
                ]
            )
            image_summaries[file_name].append((img_name, msg.content))

    return image_summaries


def create_multi_vector_retriever(
    vectorstore: PGVector,
    text_summaries_dict: dict[str, list[str]],
    texts_dict: dict[str, list[str]],
    table_summaries_dict: dict[str, list[str]],
    tables_dict: dict[str, list[str]],
    image_summaries_dict: dict[str, list[tuple[str, str]]],
    images_dict: dict[str, list[tuple[str, str]]],
) -> MultiVectorRetriever:
    """
    Create retriever that indexes summaries, but returns raw images or texts
    All inputs are dictionaries keyed by file names
    """
    # Initialize the storage layer
    id_key = "document_id"

    redis_url = config.REDIS_URL
    redis_host, redis_port = redis_url.split("redis://")[1].split(":")
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

    store = RedisStore(client=redis_client, namespace="multimodalrag")

    # Create the multi-vector retriever
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        id_key=id_key,
        docstore=store,
    )

    # Helper function to add documents to the vectorstore and docstore
    def add_documents(
        retriever: MultiVectorRetriever,
        doc_summaries: list[str],
        doc_contents: list[str],
        file_name: str,
    ) -> None:
        doc_ids = [str(uuid.uuid4()) for _ in doc_contents]
        summary_docs = [
            Document(
                page_content=s, metadata={id_key: doc_ids[i], "file_name": file_name, "index": i}
            )
            for i, s in enumerate(doc_summaries)
        ]
        retriever.vectorstore.add_documents(summary_docs)
        print(f"Added {len(summary_docs)} summaries to the vectorstore")
        retriever.docstore.mset(list(zip(doc_ids, doc_contents, strict=False)))
        print(f"Added {len(doc_contents)} documents to the docstore")

    # Process each file's content
    for file_name in text_summaries_dict.keys():
        # Add texts if available
        if text_summaries_dict.get(file_name):
            add_documents(
                retriever, text_summaries_dict[file_name], texts_dict[file_name], file_name
            )

        # Add tables if available
        if table_summaries_dict.get(file_name):
            add_documents(
                retriever, table_summaries_dict[file_name], tables_dict[file_name], file_name
            )

        # Add images if available
        if image_summaries_dict.get(file_name):
            # Extract summaries and images separately from tuples
            summaries = [summary for _, summary in image_summaries_dict[file_name]]
            images = [img_data for _, img_data in images_dict[file_name]]
            add_documents(retriever, summaries, images, file_name)

    return retriever


def run_multimodal_ingestion() -> None:
    embeddings = AzureOpenAIEmbeddings(
        model="text-embedding-ada-002",
        azure_endpoint=config.OAI_ENDPOINT,
        api_key=config.OAI_API_KEY,
    )

    vectorstore = PGVector(
        connection_string=f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}",
        embedding_function=embeddings,
        collection_name="knowledge_base",
    )

    model = AzureChatOpenAI(
        model="gpt-4o",
        max_tokens=2048,
        temperature=0,
        azure_endpoint=config.OAI_ENDPOINT,
        api_key=config.OAI_API_KEY,
        api_version="2024-06-01",
    )

    data_folder = config.PROCESSED_DATA_FOLDER
    texts_dict, tables_dict, images_dict = load_serialized_data(data_folder)

    text_summaries_dict, table_summaries_dict = generate_text_summaries(
        texts_dict, tables_dict, summarize_texts=True, model=model
    )
    image_summaries_dict = generate_img_summaries(images_dict, model=model)

    _ = create_multi_vector_retriever(
        vectorstore,
        text_summaries_dict,
        texts_dict,
        table_summaries_dict,
        tables_dict,
        image_summaries_dict,
        images_dict,
    )

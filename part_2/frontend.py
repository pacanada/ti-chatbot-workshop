from operator import itemgetter

import chainlit as cl
import redis
from _config import Config
from _utils import is_image_data, looks_like_base64, resize_base64_image
from chainlit.element import Element
from chainlit.input_widget import InputWidget, Slider
from langchain.memory import ConversationBufferMemory
from langchain.retrievers import MultiVectorRetriever
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableSerializable
from langchain.schema.runnable.config import RunnableConfig
from langchain_community.storage import RedisStore
from langchain_community.vectorstores import PGVector
from langchain_core.documents.base import Document
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

config = Config()


widgets: list[InputWidget] = [
    Slider(
        id="Temperature",
        label="OpenAI - Temperature",
        initial=0.0,
        min=0.0,
        max=2.0,
        step=0.1,
        tooltip="Adjust the randomness of the LLM's responses.",
        description="Lower values (e.g., 0.2) make the output focused and deterministic, while higher values (e.g., 1.0) produce more diverse and random outputs.",
    ),
    Slider(
        id="Num_Documents_To_Retrieve",
        label="Number of Documents to Retrieve",
        initial=3,
        min=1,
        max=10,
        step=1,
        tooltip="Set the number of documents to retrieve for each query.",
        description="A higher number will retrieve more documents, but may slow down response times and make the output more complex.",
    ),
]

embeddings = AzureOpenAIEmbeddings(
    model="text-embedding-ada-002",
    api_key=config.OAI_API_KEY,
    azure_endpoint=config.OAI_ENDPOINT,
    api_version="2024-06-01",
)

vectorstore = PGVector(
    connection_string=f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}",
    embedding_function=embeddings,
    collection_name="knowledge_base",
)
# Initialize the storage layer
id_key = "document_id"

redis_url = config.REDIS_URL
redis_host, redis_port = redis_url.split("redis://")[1].split(":")
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

docstore = RedisStore(client=redis_client, namespace="multimodalrag")


def split_image_text_types(docs: list[Document]) -> dict[str, list]:
    """
    Split base64-encoded images and texts
    """
    b64_images = []
    texts = []
    for doc in docs:
        # Check if the document is of type Document and extract page_content if so
        if isinstance(doc, Document):
            doc_content = doc.page_content
            doc_metadata = doc.metadata
        else:
            doc_content = doc
            doc_metadata = {}

        if looks_like_base64(doc_content) and is_image_data(doc_content):
            buf, doc_content = resize_base64_image(doc_content, size=(1300, 600))
            b64_images.append(doc_content)
            images = cl.user_session.get("retrieved_images")
            if images:
                images.append(buf)
                cl.user_session.set("retrieved_images", images)
            else:
                cl.user_session.set("retrieved_images", [buf])
        else:
            texts.append({"content": doc_content, "metadata": doc_metadata})
            stored_texts = cl.user_session.get("retrieved_texts")
            if stored_texts:
                stored_texts.append({"content": doc_content, "metadata": doc_metadata})
                cl.user_session.set("retrieved_texts", stored_texts)
            else:
                cl.user_session.set(
                    "retrieved_texts", [{"content": doc_content, "metadata": doc_metadata}]
                )
    return {"images": b64_images, "texts": texts}


def img_prompt_func(data_dict: dict) -> list[HumanMessage]:
    """
    Join the context into a single string
    """
    formatted_texts = "\n".join([text["content"] for text in data_dict["context"]["texts"]])
    messages = []

    # Adding the text for analysis
    text_message = {
        "type": "text",
        "text": (
            "You are an assistant for a company called DFDS.\n"
            "You will be given a mixed of text, tables, and image(s) usually of charts or graphs.\n"
            "Use this information to answer the question made by the user. \n"
            f"Chat History: {data_dict['history']}\n\n"
            f"User-provided question: {data_dict['question']}\n\n"
            "Text and / or tables:\n"
            f"{formatted_texts}"
        ),
    }
    messages.append(text_message)
    # Adding image(s) to the messages if present
    if data_dict["context"]["images"]:
        for image in data_dict["context"]["images"]:
            image_message = {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{image}",
            }
            messages.append(image_message)
    return [HumanMessage(content=str(messages))]


def multi_modal_rag_chain(
    retriever: MultiVectorRetriever, temp: float = 0.0, max_tokens: int = 1024
) -> RunnableSerializable:
    """
    Multi-modal RAG chain
    """

    # Multi-modal LLM
    model = AzureChatOpenAI(
        model="gpt-4o",
        max_tokens=2048,
        temperature=0,
        azure_endpoint=config.OAI_ENDPOINT,
        api_key=config.OAI_API_KEY,
        streaming=True,
    )
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory
    # RAG pipeline
    chain: RunnableSerializable = (
        {
            "context": retriever | RunnableLambda(split_image_text_types),
            "question": RunnablePassthrough(),
            "history": RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
        }
        | RunnableLambda(img_prompt_func)
        | model
        | StrOutputParser()
    )

    return chain


@cl.on_chat_start
async def setup() -> None:
    msg = cl.Message(content="Loading. `Please Wait`...")
    settings = await cl.ChatSettings(widgets).send()
    await msg.send()
    cl.user_session.set("settings", settings)
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    # Create the multi-vector retriever
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        id_key=id_key,
        search_kwargs={
            "k": int(settings["Num_Documents_To_Retrieve"]),
        },
    )
    runnable = multi_modal_rag_chain(retriever)
    cl.user_session.set("runnable", runnable)
    # Add a welcome message with instructions on how to use the chatbot
    welcome_message = (
        "Hello\n"
        "Welcome to the RAG Chatbot Powered by the GPT-4o with Vision 🤖! "
        "Here's how you can interact with it:\n\n"
        "1. Use the **sliders and switches** on the left to adjust the settings.\n"
        "2. Type your query in the **input box at the bottom**. This mode uses a multimodal RAG that includes tables and images, which are sent to gpt-4o for processing and response generation.\n"
        "3. The application will process your query and provide a response with the texts and images that were used to generate a response.\n\n"
        "Now, please type your query to start a conversation."
    )

    msg.content = welcome_message
    await msg.update()


@cl.on_settings_update
async def change_settings(settings: dict) -> None:
    settings = cl.user_session.get("settings")
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        id_key=id_key,
        search_kwargs={
            "k": int(settings["Num_Documents_To_Retrieve"]),
        },
    )
    runnable = multi_modal_rag_chain(retriever, float(settings["Temperature"]))
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def handle_new_message(message: cl.Message) -> None:
    runnable = cl.user_session.get("runnable")  # type: RunnableLambda
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory
    cl.user_session.set("retrieved_images", None)
    cl.user_session.set("retrieved_texts", None)

    res = cl.Message(content="")

    async for chunk in runnable.astream(
        message.content,
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)

    await res.send()

    ret_images = cl.user_session.get("retrieved_images")
    ret_texts = cl.user_session.get("retrieved_texts")
    elements: list[Element] = []
    if ret_images:
        for i, img in enumerate(ret_images):
            elements.append(
                cl.Image(
                    content=img,
                    name=f"Image {i + 1}",
                    display="inline",
                )
            )
    if ret_texts:
        for i, text in enumerate(ret_texts):
            elements.append(
                cl.Text(
                    content=text["content"],
                    name=f"Text {i + 1}",
                    display="inline",
                )
            )
    res.elements = elements
    await res.update()

    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content)
    cl.user_session.set("memory", memory)

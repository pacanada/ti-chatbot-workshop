import json
from pathlib import Path

import psycopg2
import tiktoken
from _config import Config, logger
from openai import AzureOpenAI

config = Config()


class EmbeddingModel:
    def __init__(self) -> None:
        self.client = AzureOpenAI(
            api_key=config.OAI_API_KEY,
            azure_endpoint=config.OAI_ENDPOINT,
            api_version="2024-06-01",
        )
        self.tiktoken_model = tiktoken.encoding_for_model("text-embedding-ada-002")

    def split_text_to_chunks(self, text: str, chunk_size_tokens: int = 1000) -> list[str]:
        """Naive implementation where given text is split by double newlines (paragraphs).
        Max tokens is 8192"""
        chunks = []
        chunk = ""
        for line in text.split("\n\n"):
            if len(self.tiktoken_model.encode(chunk + line)) > chunk_size_tokens:
                chunks.append(chunk)
                chunk = line
            else:
                chunk += line
        chunks.append(chunk)
        return chunks

    def get_embedding(self, texts_to_embed: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model="text-embedding-ada-002", input=texts_to_embed, dimensions=1536
        )
        return [item.embedding for item in response.data]


def basic_extract_demo() -> None:
    # Load all text files from the data folders
    data = {}
    em = EmbeddingModel()

    logger.info("Loading text files...")
    for file in (Path(__file__).parent / config.RAW_DATA_FOLDER).glob("*.txt"):
        with open(file, encoding="utf-8") as f:
            data[file.stem] = f.read()

    def get_embeddings(text: str) -> dict[str, list[float]]:
        chunks = em.split_text_to_chunks(text, 500)
        embeddings = em.get_embedding(chunks)
        return dict(zip(chunks, embeddings, strict=False))

    def process_file(file_name: str, text: str) -> tuple[str, dict[str, list[float]]]:
        return file_name, get_embeddings(text)

    embeddings = {}
    for file_name, text in data.items():
        logger.info(f"Processing {file_name}...")
        _, embedding = process_file(file_name, text)
        embeddings[file_name] = embedding

    with psycopg2.connect(
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
    ) as conn:
        with conn.cursor() as cur:
            logger.info("Inserting embeddings into the database...")
            for document_id, embeddings_ in embeddings.items():
                id_ = 0
                for text, embedding in embeddings_.items():
                    cur.execute(
                        """
                        INSERT INTO knowledge_base (document_id, embedding, additional_information, text)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (document_id) DO UPDATE
                        SET embedding = EXCLUDED.embedding,
                            additional_information = EXCLUDED.additional_information,
                            text = EXCLUDED.text
                        """,
                        (
                            f"{document_id}_{id_}",
                            embedding,
                            json.dumps({"document_id": document_id}),
                            text,
                        ),
                    )
                    id_ += 1
            conn.commit()


if __name__ == "__main__":
    basic_extract_demo()

import psycopg2
import tiktoken
from openai import AzureOpenAI

from common.config import Config

config = Config()


class Chatbot:
    def __init__(self) -> None:
        self.client = AzureOpenAI(
            api_key=config.OAI_API_KEY,
            azure_endpoint=config.OAI_ENDPOINT,
            api_version="2024-06-01",
        )
        self.system_message = """You are a historical chatbot. You will be asked questions about historical people and events,
and you will be provided with textbook context. Please use this context explicitly and even quote the book if you can while answering.

After each paragraph if you cited or referred to anything from the context please finish the paragraph by using (Book <book name_id>).
        
        Context: """
        self.knowledge_context: dict[str, str] = dict()

    def _lookup_in_textbook(self, text: str) -> dict[str, str]:
        """Lookup the text in the textbook and return the relevant context."""
        question_embedding = EmbeddingModel().get_embedding(text)

        with psycopg2.connect(
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
        ) as conn:
            with conn.cursor() as cur:
                vector_search_query = "SELECT document_id, text FROM knowledge_base ORDER BY embedding <-> %s::vector LIMIT 3;"
                cur.execute(vector_search_query, (question_embedding,))
                results = cur.fetchall()
                if not results:
                    return {"": ""}
        return {result[0]: result[1] for result in results}

    def _get_knowledge_context_str(self) -> str:
        return "\n\n".join(
            [f"Book {doc_id}: {text}" for doc_id, text in self.knowledge_context.items()]
        )

    def chat(self, user_message: str) -> tuple[dict[str, str], str | None]:
        try:
            self.knowledge_context.update(self._lookup_in_textbook(user_message))
        except Exception:
            self.knowledge_context = dict()

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": self.system_message + self._get_knowledge_context_str(),
                },
                {"role": "user", "content": user_message},
            ],
        )
        return self.knowledge_context, response.choices[0].message.content


class EmbeddingModel:
    def __init__(self) -> None:
        self.client = AzureOpenAI(
            api_key=config.OAI_API_KEY,
            azure_endpoint=config.OAI_ENDPOINT,
            api_version="2023-05-15",
        )
        self.tiktoken_model = tiktoken.encoding_for_model("text-embedding-ada-002")

    def split_text_to_chunks(self, text: str, chunk_size_tokens: int = 1000) -> list[str]:
        """Naive implementation where given text is split by double newlines (paragraphs).
        Max tokens is 8192

        TODO: Use something pre-built like haystack?"""
        # Replace all multiple spaces with a single space
        text = " ".join(text.split(sep="      "))

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

    def get_embedding(self, text_to_embed: str) -> list[float]:
        response = self.client.embeddings.create(
            model="text-embedding-ada-002", input=text_to_embed, dimensions=1536
        )
        return response.data[0].embedding

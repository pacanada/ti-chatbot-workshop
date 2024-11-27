import psycopg2
from _config import Config, logger
from _get_text import EmbeddingModel
from openai import AzureOpenAI

config = Config()


class Chatbot:
    def __init__(self) -> None:
        self.client = AzureOpenAI(
            api_key=config.OAI_API_KEY,
            azure_endpoint=config.OAI_ENDPOINT,
            api_version="2024-06-01",
        )
        self.system_message = """You are an assistant that answers questions based on provided context. 
        If you need more information, please ask. You speak like Jack Sparrow, the pirate captain. 

        Please provide the context you used at the end of a given paragraph as (_name_).
    
        Context: """
        self.knowledge_context: dict[str, str] = dict()
        self.number_of_contexts: int = 1

    def _lookup_in_textbook(self, text: str) -> dict[str, str]:
        """Lookup the text in the textbook and return the relevant context."""
        question_embedding = EmbeddingModel().get_embedding(text)[0]

        with psycopg2.connect(
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
        ) as conn:
            with conn.cursor() as cur:
                vector_search_query = f"SELECT document_id, text FROM knowledge_base ORDER BY embedding <-> %s::vector LIMIT {self.number_of_contexts};"
                cur.execute(vector_search_query, (question_embedding,))
                results = cur.fetchall()
                if not results:
                    return {"": ""}
        return {result[0]: result[1] for result in results}

    def _get_knowledge_context_str(self) -> str:
        return "\n\n".join(
            [f"{doc_id}: {text}" for doc_id, text in self.knowledge_context.items()]
        )

    def chat(self, user_message: str) -> tuple[dict[str, str], str | None]:
        try:
            self.knowledge_context.update(self._lookup_in_textbook(user_message))
        except Exception as e:
            logger.exception(f"Error while looking up in textbook: {e}")
            self.knowledge_context = dict()

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": self.system_message + self._get_knowledge_context_str(),
                },
                {"role": "user", "content": user_message},
            ],
        )
        return self.knowledge_context, response.choices[0].message.content

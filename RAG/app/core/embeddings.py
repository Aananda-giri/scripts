import time

from google import genai


class GeminiEmbedder:
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def embed(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config={"task_type": task_type},
        )
        return result.embeddings[0].values

    def embed_query(self, query: str) -> list[float]:
        return self.embed(query, task_type="RETRIEVAL_QUERY")

    def embed_batch(self, texts: list[str], batch_size: int = 50,
                    retry_max: int = 3, retry_delay: float = 2.0) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for attempt in range(retry_max):
                try:
                    for text in batch:
                        emb = self.embed(text, task_type="RETRIEVAL_DOCUMENT")
                        all_embeddings.append(emb)
                    break
                except Exception as e:
                    if attempt < retry_max - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                    else:
                        raise RuntimeError(
                            f"Embedding batch {i // batch_size} failed after "
                            f"{retry_max} attempts: {e}"
                        ) from e
            if i + batch_size < len(texts):
                time.sleep(0.5)
        return all_embeddings

import time

from openai import OpenAI


class Embedder:
    def __init__(self, api_key: str, model: str = "nomic-embed-text",
                 base_url: str = "http://localhost:11434/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def embed(self, text: str) -> list[float]:
        result = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return result.data[0].embedding

    def embed_query(self, query: str) -> list[float]:
        return self.embed(query)

    def embed_batch(self, texts: list[str], batch_size: int = 50,
                    retry_max: int = 3, retry_delay: float = 2.0) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for attempt in range(retry_max):
                try:
                    result = self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                    )
                    for item in result.data:
                        all_embeddings.append(item.embedding)
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

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import (
    Distance,
    HnswConfigDiff,
    OptimizersConfigDiff,
    PayloadSchemaType,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
    VectorParams,
)


class QdrantStore:
    def __init__(self, host: str = "localhost", port: int = 6333,
                 collection_name: str = "job_chunks"):
        self.client = QdrantClient(host=host, port=port, prefer_grpc=False)
        self.collection_name = collection_name

    def create_collection(self, vector_size: int = 768, recreate: bool = False) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name in collections:
            if recreate:
                self.client.delete_collection(self.collection_name)
            else:
                return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
            optimizers_config=OptimizersConfigDiff(memmap_threshold=20000),
            quantization_config=ScalarQuantization(
                scalar=ScalarQuantizationConfig(
                    type=ScalarType.INT8, always_ram=True
                )
            ),
        )

        for field in ["job_category", "job_level", "company_name", "job_location"]:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="tags",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="publication_date",
            field_schema=PayloadSchemaType.DATETIME,
        )

    def upsert_chunks(self, chunks: list[dict],
                      vectors: list[list[float]]) -> int:
        points = []
        for chunk, vector in zip(chunks, vectors):
            payload = {k: v for k, v in chunk.items() if k != "text"}
            payload["text"] = chunk["text"]
            point = models.PointStruct(
                id=self._make_id(chunk["chunk_id"]),
                vector=vector,
                payload=payload,
            )
            points.append(point)

        for i in range(0, len(points), 100):
            batch_ids = self.client.upsert(
                collection_name=self.collection_name,
                points=points[i:i + 100],
                wait=True,
            )
        return len(points)

    def search(self, query_vector: list[float], top_k: int = 20,
               filter_cond: dict | None = None) -> list:
        query_filter = None
        if filter_cond:
            must_conditions = []
            for field, values in filter_cond.items():
                if values:
                    must_conditions.append(
                        models.FieldCondition(
                            key=field,
                            match=models.MatchAny(any=values),
                        )
                    )
            if must_conditions:
                query_filter = models.Filter(must=must_conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False,
        )
        return results

    def collection_info(self) -> dict:
        info = self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "points_count": info.points_count,
            "vectors_count": info.indexed_vectors_count,
        }

    @staticmethod
    def _make_id(chunk_id: str) -> int:
        return abs(hash(chunk_id)) % (2 ** 63)

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import datetime

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # get API keys from .env file
vector_db_url = os.environ.get("VECTOR_DB_URL")

class Vectordb:
    def __init__(self, api_key):
        self.threshold = 0 # Between 0 and 1. Only queries that have score > threshold will be returned
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant_client = QdrantClient(
            url=vector_db_url,
            api_key=api_key,
        )

    def set_threshold(self, threshold):
        self.threshold = threshold

    def create_collection(self, collection_name):
        try:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=self.encoder.get_sentence_embedding_dimension(),  # Vector size is defined by used model
                    distance=models.Distance.COSINE,
                ),
            )
        except Exception as e:
            print("Unable to create collection, database might already exist.")
            # print(e)

    def upload_docs(self, collection_name, documents, input_col):
        self.qdrant_client.upload_points(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=idx,
                    vector=self.encoder.encode(doc[input_col]).tolist(),
                    payload=doc,
                )
                for idx, doc in enumerate(documents)
            ],
        )

    def query(self, prompt, collection_name, output_col):
        # Filter outputs by threshold (score > threshold), and sorts the filtered output by date (most recent)
        def filter_and_sort_outputs(hits):
            final_hits = list(filter(lambda x: x.score > self.threshold, hits))
            final_hits.sort(key=lambda x: x.payload['date'], reverse=True)
            return final_hits

        hits = self.qdrant_client.query_points(
            collection_name=collection_name,
            query=self.encoder.encode(prompt).tolist(),
            query_filter=models.Filter(
                # must=[models.FieldCondition(key="date", range=models.DatetimeRange(gte=datetime.datetime(2018, 6, 1)))]
            ),
            limit=5, # Allow multiple outputs to filter by similarity score and sort by date
        ).points
        # Get filtered and sorted outputs
        final_hits = filter_and_sort_outputs(hits)
        if not final_hits:
            print(f"No similar query found in vectordb...")
            output = None
            score = 0
        else:
            output = final_hits[0].payload[output_col]
            score = round(hits[0].score, 2)
        return (output, score)

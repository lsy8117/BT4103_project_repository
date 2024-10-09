from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import datetime

class Vectordb:
  def __init__(self, api_key):
    self.threshold = 1
    self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
    self.qdrant_client = QdrantClient(
    url="https://4911e305-90e1-4135-a023-39320bdb1588.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key=api_key
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
          id=idx, vector=self.encoder.encode(doc[input_col]).tolist(), payload=doc
        )
        for idx, doc in enumerate(documents)
      ],
      )
  def query(self, prompt, collection_name, output_col):
    hits = self.qdrant_client.query_points(
      collection_name=collection_name,
      query=self.encoder.encode(prompt).tolist(),
      query_filter=models.Filter(
          # must=[models.FieldCondition(key="date", range=models.DatetimeRange(gte=datetime.datetime(2018, 6, 1)))]
      ),
      limit=1,
    ).points
    ## For multiple similar outputs
    # for hit in hits:
    #     print(hit.payload[output_col], "score:", hit.score)

    ## For most relevant output
    output = hits[0].payload[output_col]
    score = round(hits[0].score, 2)
    if score < self.threshold:
      print(f"No similar query. Similarty score = {score} < {self.threshold}")
      output = None
    return (output, score)
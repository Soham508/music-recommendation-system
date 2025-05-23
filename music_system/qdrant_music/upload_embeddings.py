import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client import models  
from qdrant_client.models import Distance

# Connecting to local Qdrant instance
client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "music_recommendations"

# Loading the embeddings and metadata
print("Loading embeddings and metadata...")
final_embeddings = np.load("final_embeddings.npy")
metadata_df = pd.read_csv("song_metadata.csv")
payloads = metadata_df.apply(lambda row: row.to_dict(), axis=1).tolist()

# Creating collection if it doesn't exist
vector_size = final_embeddings.shape[1]

try:
    client.get_collection(COLLECTION_NAME)
    print(f" Collection '{COLLECTION_NAME}' already exists.")
except Exception:
    print(f" Creating collection '{COLLECTION_NAME}' with vector size {vector_size}...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={"size": vector_size, "distance": Distance.COSINE}
    )

# Prepare points
print(f" Preparing {len(final_embeddings)} points for upload...")
points = [
    models.PointStruct(id=int(i), vector=final_embeddings[i].tolist(), payload=payloads[i])
    for i in range(len(final_embeddings))
]

# Uploading in batches
BATCH_SIZE = 256
for i in range(0, len(points), BATCH_SIZE):
    batch = points[i:i + BATCH_SIZE]
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(
            ids=[point.id for point in batch],
            vectors=[point.vector for point in batch],
            payloads=[point.payload for point in batch]
        )
    )
    print(f"Uploaded {min(i + BATCH_SIZE, len(points))}/{len(points)} songs")

print("All data uploaded to Qdrant!")

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Song, UserActivity
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointStruct
import numpy as np

User = get_user_model()

SONG_COLLECTION = "music_recommendations"
USER_COLLECTION = "users_recommendations"

EMOTIONS = ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise']
TAGS = [
    'party', 'work', 'relaxation', 'exercise', 'running', 'yoga',
    'driving', 'social gathering', 'morning_routine'
]

class Command(BaseCommand):
    help = "Generate or refresh user-embedding vectors in Qdrant"

    def handle(self, *args, **options):
        client = QdrantClient(host="localhost", port=6333)

        collection_info = client.get_collection(SONG_COLLECTION)
        song_dim = collection_info.config.params.vectors.size

        metadata_dim = len(EMOTIONS) + len(TAGS)
        user_dim = song_dim + metadata_dim

        client.recreate_collection(
            collection_name=USER_COLLECTION,
            vectors_config=qmodels.VectorParams(size=user_dim, distance=qmodels.Distance.COSINE),
        )
        self.stdout.write(self.style.SUCCESS(f"Created collection '{USER_COLLECTION}' with dimension {user_dim}."))

        points = []
        for user in User.objects.all():
            activities = UserActivity.objects.filter(user=user).order_by('-rating', '-timestamp')[:5]
            if activities.count() < 5:
                self.stdout.write(f"Skipping user {user.username}: not enough activities.")
                continue

            song_ratings = {activity.song.song: activity.rating for activity in activities}
            top_song_ids = list(song_ratings.keys())

            # Geting vectors from Qdrant
            results, _ = client.scroll(
                collection_name=SONG_COLLECTION,
                scroll_filter=Filter(should=[
                    FieldCondition(key="song", match=MatchValue(value=song)) for song in top_song_ids
                ]),
                limit=5,
                with_vectors=True,
                with_payload=True
            )

            # Matching only songs found in Qdrant
            matched_vectors = []
            matched_ratings = []
            matched_song_ids = []

            for point in results:
                song_id = point.payload.get("song")
                if song_id in song_ratings:
                    matched_vectors.append(point.vector)
                    matched_ratings.append(song_ratings[song_id])
                    matched_song_ids.append(song_id)

            if len(matched_vectors) < 5:
                self.stdout.write(f"Skipping {user.username}: only {len(matched_vectors)} matched vectors found.")
                continue

            vectors = np.array(matched_vectors)
            weights = np.array(matched_ratings, dtype=float)
            weights = weights / weights.sum()

            song_vector = np.average(vectors, axis=0, weights=weights)

            # Encoding user metadata
            emo_oh = np.array([1.0 if e in user.emotions else 0.0 for e in EMOTIONS], dtype=float)
            tag_oh = np.array([1.0 if t in user.tags else 0.0 for t in TAGS], dtype=float)
            meta_vector = np.concatenate([emo_oh, tag_oh])

            # Final user vector
            user_vector = np.concatenate([song_vector, meta_vector]).astype(float).tolist()

            payload = {
                "username": user.username,
                "emotions": user.emotions,
                "tags": user.tags,
                "last_updated": timezone.now().isoformat(),
                "top_songs": matched_song_ids
            }

            points.append(PointStruct(id=user.id, vector=user_vector, payload=payload))

        if points:
            client.upsert(collection_name=USER_COLLECTION, points=points)
            self.stdout.write(self.style.SUCCESS(f"Inserted {len(points)} user vectors to '{USER_COLLECTION}'"))
        else:
            self.stdout.write("No user vectors inserted.")

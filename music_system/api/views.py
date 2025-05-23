from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer
from .models import User
from django.contrib.auth import get_user_model
from api.models import Song, UserActivity
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from django.db.models import Q, F, FloatField, Value as V
from django.db.models.functions import Greatest


User = get_user_model()
client = QdrantClient(host="localhost", port=6333)
collection_name = "music_recommendations"


# api/views.py

import requests
import numpy as np
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.models import Song, UserActivity
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Filter, FieldCondition, MatchValue, PointStruct
)

User = get_user_model()

# Qdrant collection names
SONG_COLLECTION = "music_recommendations"
USER_COLLECTION = "users_recommendations"

# Must match your metadata-encoding vocab
EMOTIONS = ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise']
TAGS = [
    'party', 'work', 'relaxation', 'exercise', 'running', 'yoga',
    'driving', 'social gathering', 'morning_routine'
]

TAG_FIELD_MAP = {
    'party': 'good_for_party',
    'work': 'good_for_work_study',
    'relaxation': 'good_for_relaxation',
    'exercise': 'good_for_exercise',
    'running': 'good_for_running',
    'yoga': 'good_for_yoga',
    'driving': 'good_for_driving',
    'social gathering': 'good_for_social',
    'morning_routine': 'good_for_morning'
}

QDRANT = QdrantClient(host="localhost", port=6333)
CONTENT_API = "http://localhost:8000/api/recommendations/content-based/{}/"

#----------------------------------------------------------------------------------------------------------------------

class CollaborativeFilteringRecommendationView(APIView):
    def get(self, request, username):
        # Lookup for user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Trying to fetch existing user vector
        scroll_res, _ = QDRANT.scroll(
            collection_name=USER_COLLECTION,
            scroll_filter=Filter(
                should=[FieldCondition(key="username", match=MatchValue(value=username))]
            ),
            limit=1,
            with_vectors=True,
        )
        if scroll_res:
            user_vec = np.array(scroll_res[0].vector, dtype=float)
        else:
            # if No existing vector found, building it, if possible
            acts = UserActivity.objects.filter(user=user).order_by('-rating', '-timestamp')[:5]
            if acts.count() < 5:
                return Response(
                    {"error": "Not enough activity to build user profile (need ≥5)"},
                    status=400
                )

            # fetching song vectors
            song_keys = [a.song.song for a in acts]
            results, _ = QDRANT.scroll(
                collection_name=SONG_COLLECTION,
                scroll_filter=Filter(should=[
                    FieldCondition(key="song", match=MatchValue(value=s))
                    for s in song_keys
                ]),
                limit=5,
                with_vectors=True,
            )
          
            vecs, ratings = [], []
            for pt in results:
                sid = pt.payload.get("song")
               
                for a in acts:
                    if a.song.song == sid:
                        vecs.append(pt.vector)
                        ratings.append(a.rating)
                        break

            if len(vecs) < 5:
                return Response(
                    {"error": "Could only fetch {} of 5 song vectors".format(len(vecs))},
                    status=500
                )

            V = np.array(vecs, dtype=float)
            W = np.array(ratings, dtype=float)
            W = W / W.sum()
            song_part = np.average(V, axis=0, weights=W.flatten())

            # building metadata part
            emo_oh = np.array([1.0 if e in user.emotions else 0.0 for e in EMOTIONS], dtype=float)
            tag_oh = np.array([1.0 if t in user.tags else 0.0 for t in TAGS], dtype=float)
            meta_part = np.concatenate([emo_oh, tag_oh])

         
            user_vec = np.concatenate([song_part, meta_part]).tolist()

            # upserting into Qdrant
            payload = {
                "username": user.username,
                "emotions": user.emotions,
                "tags": user.tags,
                "last_updated": timezone.now().isoformat(),
                "top_songs": song_keys
            }
            QDRANT.upsert(
                collection_name=USER_COLLECTION,
                points=[PointStruct(id=user.id, vector=user_vec, payload=payload)]
            )

        # Finding closest user
        neighbors = QDRANT.search(
            collection_name=USER_COLLECTION,
            query_vector=user_vec,
            query_filter=Filter(
                must_not=[FieldCondition(key="username", match=MatchValue(value=username))]
            ),
            limit=1,
        )
        if not neighbors:
            return Response({"error": "No similar user found"}, status=404)

        closest = neighbors[0].payload.get("username")

        # Getting recommendations for the closest user

        
        print('Username of closest user:', closest)
        
        recommendation_data = generate_content_based_recommendations(closest)
        if "error" in recommendation_data:
            return Response({
                "error": "Content-based recommendation failed",
                "details": recommendation_data
            }, status=502)
        
        return Response({
            "user": username,
            "most_similar_user": closest,
            "recommendations": recommendation_data["recommendations"]
        })

#----------------------------------------------------------------------------------------------------------------------

class ContentBasedRecommendationView(APIView):
    def get(self, request, username):
        result = generate_content_based_recommendations(username)
        status_code = result.pop("status", 200)
        return Response(result, status=status_code)

def generate_content_based_recommendations(username):
    # Getting the user
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return {
            "error": "User not found",
            "status": 404
        }

    # Getting top 5 relevant interactions based on, high rating + recency
    top_activities = UserActivity.objects.filter(user=user).order_by('-rating', '-timestamp')[:5]
    if not top_activities.exists():
        return {
            "error": "No activity found for this user.",
            "status": 404
        }

    top_songs = [activity.song.song for activity in top_activities]

    # Querying Qdrant for those 5 songs
    try:
        results, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(should=[
                FieldCondition(key="song", match=MatchValue(value=song)) for song in top_songs
            ]),
            limit=5,
            with_vectors=True,
            with_payload=True
        )
    except Exception as e:
        return {
            "error": "Failed to query Qdrant for song vectors.",
            "details": str(e),
            "status": 500
        }

    if not results:
        return {
            "error": "No matching songs found in Qdrant",
            "status": 404
        }

    
    try:
        vectors = np.array([point.vector for point in results])
        ratings = np.array([[activity.rating] for activity in top_activities])
        weights = ratings / ratings.sum()
        preference_vector = np.average(vectors, axis=0, weights=weights.flatten()).tolist()
    except Exception as e:
        return {
            "error": "Error building preference vector.",
            "details": str(e),
            "status": 500
        }

    #  Searching for similar songs
    try:
        similar_results = client.search(
            collection_name=collection_name,
            query_vector=preference_vector,
            query_filter=Filter(must_not=[
                FieldCondition(key="song", match=MatchValue(value=song)) for song in top_songs
            ]),
            limit=10
        )
    except Exception as e:
        return {
            "error": "Error performing vector search in Qdrant.",
            "details": str(e),
            "status": 500
        }

    # Removing duplicates if any exists
    filtered_results = [
        r for r in similar_results
        if r.payload['song'] not in top_songs
    ][:5]

    if not filtered_results:
        return {
            "error": "No similar songs found.",
            "status": 404
        }

    try:
        recommended_songs = Song.objects.filter(song__in=[r.payload['song'] for r in filtered_results])
        recommended_data = [
            {
                'song': song.song,
                'artist': song.artist,
                'genre': song.genre,
                'emotion': song.emotion,
                'release_year': int(song.release_year),
                'score': next(r.score for r in filtered_results if r.payload['song'] == song.song)
            } for song in recommended_songs
        ]
    except Exception as e:
        return {
            "error": "Failed to build final recommendation list.",
            "details": str(e),
            "status": 500
        }

    return {
        "user": username,
        "top_interactions": top_songs,
        "recommendations": recommended_data,
        "status": 200
    }

#----------------------------------------------------------------------------------------------------------------------

class KnowledgeBasedRecommendationView(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user_emotions = user.emotions or []
        user_tags = user.tags or []

        if not user_emotions and not user_tags:
            return Response({"message": "User has no prior emotion or tag preferences"}, status=400)

        # Filtering by emotion
        emotion_filter = Q()
        if user_emotions:
            emotion_filter = Q(emotion__in=user_emotions)

        # Tag relevant score dynamically
        annotations = {}
        tag_score_exprs = []
        for tag in user_tags:
            field = TAG_FIELD_MAP.get(tag)
            if field:
                annotations[field] = F(field)
                tag_score_exprs.append(F(field))

        if not tag_score_exprs:
            tag_score_exprs = [V(0.0)]

        # Combining queries
        songs_qs = Song.objects.filter(emotion_filter).annotate(
            tag_score=Greatest(*tag_score_exprs),
        ).order_by('-tag_score')[:10]

        if not songs_qs.exists():
            return Response({"message": "No matching songs found based on knowledge rules"}, status=404)

       
        recommendations = [
            {
                "song": song.song,
                "artist": song.artist,
                "genre": song.genre,
                "emotion": song.emotion,
                "release_year": int(song.release_year),
                "tag_score": round(song.tag_score, 2),
            }
            for song in songs_qs[:5]
        ]

        return Response({
            "user": username,
            "emotions": user_emotions,
            "tags": user_tags,
            "recommendations": recommendations
        })

#----------------------------------------------------------------------------------------------------------------------

# User model APIs

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)  #authenticates user
        if user is not None:
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({"error": "User account is disabled."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"message": "User account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


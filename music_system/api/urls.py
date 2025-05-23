from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, ContentBasedRecommendationView, CollaborativeFilteringRecommendationView, KnowledgeBasedRecommendationView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('users/register/', RegisterView.as_view(), name='register'),
    path('users/login/', LoginView.as_view(), name='login'),
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('recommendations/content-based/<str:username>/', ContentBasedRecommendationView.as_view(), name='content_based_recommendation'),
    path('recommendations/collaborative-filtering/<str:username>/', CollaborativeFilteringRecommendationView.as_view(), name='collaborative_filtering_recommendation'),
    path('recommendations/knowledge-based/<str:username>/', KnowledgeBasedRecommendationView.as_view(), name='knowledge_based_recommendation'),
]

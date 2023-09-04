from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.apps import ApiConfig
from api.views import (
    CategoryViewSet,
    CommentViewSet,
    GenreViewSet,
    ReviewViewSet,
    TitleViewSet,
    UserViewSet,
    create_token,
    signup,
)

app_name = ApiConfig.name

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('titles', TitleViewSet)
router.register('categories', CategoryViewSet)
router.register('genres', GenreViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments',
)


urlpatterns = [
    path('auth/signup/', signup, name='signup'),
    path('auth/token/', create_token, name='create-token'),
    path('', include(router.urls)),
]

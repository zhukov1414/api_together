from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import AccessToken

from api.filters import TitleFilter
from api.mixins import ListCreateDestroyMixin
from api.permissions import (
    IsAdminPermission,
    IsAuthorOrModeratorOrAdminOrReadOnlyPermission,
    OnlyAdminCanEditPermission,
)
from api.serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    ReviewSerializer,
    SignUpSerializer,
    TitleGetSerializer,
    TitleSerializer,
    TokenObtainSerializer,
    UserSerializer,
)
from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()


def create_and_send_token(user, email):
    token = default_token_generator.make_token(user)
    send_mail(
        'Код подтверждения',
        f'Код подтверждения для пользователя с почтой {email}: {token}.',
        settings.EMAIL_ADRESS,
        [email],
        fail_silently=True,
    )


@api_view(['POST'])
def signup(request):
    serializer = SignUpSerializer(data=request.data)
    if User.objects.filter(
        username=request.data.get('username'),
        email=request.data.get('email'),
    ).exists():
        user = User.objects.get(email=request.data.get('email'))
        create_and_send_token(user, request.data.get('email'))
        return Response(request.data, status=status.HTTP_200_OK)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        user, _status = User.objects.get_or_create(
            username=username, email=email
        )
        create_and_send_token(user, email)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_token(request):
    serializer = TokenObtainSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    confirmation_code = serializer.validated_data['confirmation_code']
    user = get_object_or_404(User, username=username)

    if default_token_generator.check_token(user, confirmation_code):
        token = AccessToken.for_user(user).get('jti')
        return Response({'token': token}, status=status.HTTP_200_OK)
    response = {'confirmation_code': 'Неверный код подтверждения'}
    return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminPermission,)
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    http_method_names = ('get', 'patch', 'delete', 'post')
    search_fields = ('username',)

    @action(
        methods=('get', 'patch'),
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='me',
    )
    def edit_self_user(self, request, *args, **kwargs):
        user = get_object_or_404(User, username=self.request.user)
        serializer = UserSerializer(user)
        if self.request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(role=user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TitleViewSet(ModelViewSet):
    queryset = (
        Title.objects.all().annotate(Avg('reviews__score')).order_by('name')
    )
    serializer_class = TitleSerializer
    permission_classes = (OnlyAdminCanEditPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TitleGetSerializer
        return TitleSerializer


class CategoryViewSet(ListCreateDestroyMixin):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = (OnlyAdminCanEditPermission,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class GenreViewSet(ListCreateDestroyMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    permission_classes = (OnlyAdminCanEditPermission,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorOrModeratorOrAdminOrReadOnlyPermission,)

    def get_queryset(self):
        return get_object_or_404(Title,
                                 id=self.kwargs.get
                                 ('title_id')).reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        title=get_object_or_404(Title,
                                                id=self.kwargs.get
                                                ('title_id')))


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrModeratorOrAdminOrReadOnlyPermission,)

    def get_queryset(self):
        return get_object_or_404(Review,
                                 id=self.kwargs.get
                                 ('review_id')).comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        review=get_object_or_404(Review,
                                                 id=self.kwargs.get
                                                 ('review_id')))

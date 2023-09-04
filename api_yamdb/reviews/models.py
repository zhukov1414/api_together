from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from reviews.validators import validate_username, validate_datetime


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLES = [
        (ADMIN, 'Administrator'),
        (MODERATOR, 'Moderator'),
        (USER, 'User'),
    ]
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=(validate_username,),
    )
    email = models.EmailField(
        verbose_name='email пользователя',
        max_length=254,
        unique=True,
    )
    bio = models.TextField(
        verbose_name='Биография пользователя',
        blank=True,
    )
    role = models.CharField(
        verbose_name='Роль пользователя',
        max_length=50,
        choices=ROLES,
        default=USER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'), name='unique_pair'
            ),
        ]

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser


class ClassificatorModel(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Адрес')

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Genre(ClassificatorModel):
    class Meta:
        verbose_name = 'Жанр'


class Category(ClassificatorModel):
    class Meta:
        verbose_name = 'Категория'


class Title(models.Model):
    name = models.CharField(
        max_length=256, verbose_name='Название произведения'
    )
    year = models.PositiveSmallIntegerField(
        validators=(validate_datetime, ),
        null=True,
        verbose_name='Год создания произведения',
    )
    description = models.TextField(verbose_name='Описание произведения')
    genre = models.ManyToManyField(
        Genre, related_name='titles', verbose_name='Жанр произведения'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='titles',
        blank=True,
        null=True,
        verbose_name='Категория произведения',
    )

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Оцениеваемое произведение',
    )
    author = models.ForeignKey(
        User,
        max_length=50,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор отзыва',
    )
    text = models.TextField(verbose_name='Текст отзыва')
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
        verbose_name='Оценка',
    )
    pub_date = models.DateField(
        auto_now_add=True, db_index=True, verbose_name='Дата публикации'
    )

    def __str__(self):
        return self.title_id

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'], name='unique_review'
            )
        ]


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментируемая оценка',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор комментария'
    )
    text = models.TextField(verbose_name='Текст комментария')
    pub_date = models.DateField(
        auto_now_add=True, db_index=True, verbose_name='Дата публикации'
    )

    def __str__(self):
        return self.review

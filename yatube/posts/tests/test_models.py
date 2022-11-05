from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ..models import Group, Post, User
from .test_views import SMALL_GIF, TEMP_MEDIA_ROOT


import shutil
import tempfile


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='group_1',
            description='Тестовое описание группы 1',
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )        
        cls.post = Post.objects.create(
            text='Текст тестового поста 1',
            author=cls.user,
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTests.group
        expected_group_title = group.title
        real_group_title = 'Тестовая группа 1'
        self.assertEqual(expected_group_title, real_group_title)

        post = PostModelTests.post
        expected_post_representation = post.text[:15]
        real_post_representation = str(post)
        self.assertEqual(
            expected_post_representation, real_post_representation
        )

    def test_verbose_name(self):
        """verbose_name в полях публикаций совпадает с ожидаемым"""
        post = PostModelTests.post
        verbose_fields = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Изображение'
        }

        for field, expected_value in verbose_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTests.post
        help_text_fields = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Добавьте изображение к посту',
        }

        for field, expected_value in help_text_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
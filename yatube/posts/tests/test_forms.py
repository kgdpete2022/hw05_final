from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .test_views import SMALL_GIF, TEMP_MEDIA_ROOT
import shutil
from ..models import Post, Group, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_nonauthor = User.objects.create_user(username='NonAuthor')
        cls.user_author = User.objects.create_user(username='Author')
        cls.anonymous_client = Client()
        cls.authorized_client_nonauthor = Client()
        cls.authorized_client_nonauthor.force_login(cls.user_nonauthor)
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.user_author)
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='group_1',
            description='Тестовое описание группы 1'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='group_2',
            description='Тестовое описание группы 2'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста 1',
            author=cls.user_author,
            group=cls.group_1,
            image=cls.image
        )


    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_authorized(self):
        """Проверка создания поста авторизованным пользователем"""
        initial_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group_1.id,
            'image': self.image,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.post.author})
        )
        self.assertEqual(Post.objects.count(), initial_count + 1)

    def test_create_post_anonymous(self):
        """Проверка создания поста неавторизованным пользователем"""
        initial_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group_1.id,
            'image': self.image,
        }
        response = self.anonymous_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        self.assertEqual(Post.objects.count(), initial_count)

    def test_edit_post_author(self):
        """Проверка редактирования поста автором этого поста
        (с изменением группы поста)"""
        form_data = {
            'text': self.post.text,
            'group': self.group_2.pk,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])


    def test_edit_post_nonauthor(self):
        """Проверка редактирования поста авторизованным пользователем,
        не являющимся автором этого поста"""
        form_data = {
            'text': self.post.text,
            'group': self.group_1.pk,
            'image': self.image,
        }
        response = self.authorized_client_nonauthor.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])


    def test_edit_post_anonymous(self):
        """Проверка редактирования поста неавторизованным пользователем"""
        form_data = {
            'text': self.post.text,
            'group': self.group_1.pk,
            'image': self.image,
        }
        response = self.anonymous_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        )

        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
  

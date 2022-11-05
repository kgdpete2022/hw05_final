from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ..models import Post, Group, User
import shutil
import tempfile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='AuthorizedUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        # Создаем авторизованного автора публикации
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем, что при обращении вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['group'], self.post.group)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_correct_context(self):
        """Тест контекста для profile."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      self.post.author.username
                                                      }))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(response.context['posts_count'], Post.objects.filter(
            author=self.post.author).count()
        )
        self.assertEqual(
            response.context['posts_list'][0],
            Post.objects.filter(author=self.post.author)[0]
        )

    def test_post_detail_correct_context(self):
        """Тест контекста для profile."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.id
                                                      }))
        post_from_context = response.context['post']
        self.assertEqual(post_from_context.text, self.post.text)
        self.assertEqual(post_from_context.pub_date, self.post.pub_date)
        self.assertEqual(post_from_context.author, self.post.author)
        self.assertEqual(post_from_context.image, self.post.image)


        self.assertEqual(response.context['posts_count'], Post.objects.filter(
            author=self.post.author).count()
        )
        self.assertEqual(
            response.context['is_author'], self.user == self.post.author
        )

    def test_post_create_correct_context(self):
        """Тест контекста для post_create."""
        response = self.authorized_client.get(reverse(
            'posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Тест контекста для post_edit."""
        response = self.authorized_author.get(reverse('posts:post_edit',
                                              kwargs={'post_id':
                                                      self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

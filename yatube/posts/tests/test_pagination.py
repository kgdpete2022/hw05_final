from django.test import TestCase
from django.urls import reverse
from ..models import Post, Group, User
from ..views import POSTS_PER_PAGE

NUMBER_OF_TEST_POSTS = 16


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group_slug',
            description='Описание тестовой группы')
        cls.test_posts = []
        for i in range(NUMBER_OF_TEST_POSTS):
            cls.test_posts.append(Post(
                text=f'Тестовый пост {i+1}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.test_posts)

    def test_paginator(self):
        """Тест работы паджинатора на главной странице,
        странице группы и странице профиля """
        tested_urls = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author}),
        }

        number_of_full_pages = NUMBER_OF_TEST_POSTS // POSTS_PER_PAGE
        number_of_posts_on_last_page = NUMBER_OF_TEST_POSTS % POSTS_PER_PAGE

        for page_number in range(number_of_full_pages):
            for url in tested_urls:
                response = self.client.get(url, {'page': page_number + 1})
                self.assertEqual(len(
                    response.context.get('page_obj').object_list
                ), POSTS_PER_PAGE)
        if number_of_posts_on_last_page:
            for url in tested_urls:
                response = self.client.get(
                    url, {'page': number_of_full_pages + 1}
                )
                self.assertEqual(len(
                    response.context.get('page_obj').object_list
                ), number_of_posts_on_last_page)

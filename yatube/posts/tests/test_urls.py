from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Testuser')
        cls.not_author = User.objects.create_user(username='Notauthoruser')
        cls.post = Post.objects.create(
            author=cls.author, text='Тестовый текст')
        cls.group = Group.objects.create(title='testgroup', slug='test_slug',
                                         description='test descriptions')
        cls.templates_url_names = {
            'posts/index.html': '/',
            'posts/group.html': f'/group/{cls.group.slug}/',
            'posts/new_post.html': '/new/',
            'posts/profile.html': f'/{cls.author.username}/',
            'posts/post.html': f'/{cls.author.username}/{cls.post.id}/'}

    def setUp(self):
        self.anonim_user = Client()

        self.authorized_user = Client()
        self.authorized_user.force_login(self.author)

        self.not_author_user = Client()
        self.not_author_user.force_login(self.not_author)

    def test_urls_uses_correct_template(self):
        """URL-адрес доступность для анонимного пользователя....................
        и проверка перенаправления"""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse('new_post'):
                    response = self.anonim_user.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(response, '/auth/login/?next=/new/')
                else:
                    response = self.anonim_user.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.anonim_user.get(f'/{self.author.username}/'
                                        f'{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.anonim_user.get(
            f'/{self.author.username}/{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_author(self):
        """URL-адрес доступен автору поста......................................
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_user.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_user.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_user.get(f'/{self.author.username}/'
                                            f'{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_not_author(self):
        """URL-адрес доступен не автору поста...................................
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.not_author_user.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.not_author_user.get(f'/{self.author.username}/'
                                            f'{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.not_author_user.get(f'/{self.author.username}/'
                                            f'{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон..........................
        """
        cache.clear()
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_user.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/new_post.html')

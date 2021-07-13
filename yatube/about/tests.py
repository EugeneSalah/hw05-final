from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'}

    def setUp(self):
        self.anonim_user = Client()

    def test_urls_author(self):
        """URL-адрес страниц about и tech доступен всем пользователям...........
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.anonim_user.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон..........................
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.anonim_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

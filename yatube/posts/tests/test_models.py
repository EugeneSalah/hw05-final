from django.test import TestCase

from ..models import Group, Post, User


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.text = 'Тестовый текст больше 15 символов'
        cls.post = Post.objects.create(text=cls.text, author=cls.user)
        cls.group = Group.objects.create(title='testgroup',
                                         slug='slug')

    def test_post_name_is_text_field(self):
        """В поле __str__  объекта Post записано первых 15 символов.............
        значение поля post.text"""
        expected_text = self.post.text[:15]
        self.assertEqual(expected_text, str(self.post))

    def test_group_name_is_title_field(self):
        """В поле __str__  объекта Group записано значение поля group.title.....
        """
        expected_title = self.group.title
        self.assertEqual(expected_title, str(self.group))

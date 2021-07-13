from http import HTTPStatus

from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User

POSTS_COUNT = 13
PAGE_COUNT = 10


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')
        cls.post = Post.objects.create(
            text='Тестовый пост длинна котого больше 15 символов',
            author=cls.user, group=cls.group
        )
        cls.templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/group.html': reverse('group', kwargs={
                'slug': cls.group.slug}),
            'posts/new_post.html': reverse('new_post')
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон..........................
        """
        cache.clear()

        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_in_template_index(self):
        """Шаблон index сформирован с правильным контекстом.....................
        При создании поста с указанием группы,
        этот пост появляется на главной странице сайта.
        """
        cache.clear()
        response = self.authorized_user.get(reverse('index'))
        last_post = response.context['page'][0]
        print(dir(last_post))
        self.assertEqual(last_post, self.post)

    def test_context_in_template_group(self):
        """Шаблон group сформирован с правильным контекстом.....................
        При создании поста с указанием группы,
        этот пост появляется на странице этой группы.
        """
        response = self.authorized_user.get(reverse('group', kwargs={
            'slug': self.group.slug}))
        test_group = response.context['group']
        test_post = response.context['page'][0]
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_post, self.post)
        self.assertEqual(Post.objects.first().text, self.post.text)
        self.assertEqual(Post.objects.first().group, self.post.group)

    def test_context_in_template_new_post(self):
        """Шаблон new_posts сформирован с правильным контекстом.................
        """
        response = self.authorized_user.get(reverse('new_post'))
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField}
        for value, expect in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expect)

    def test_context_in_template_post_edit(self):
        """Шаблон post_edit сформирован с правильным контекстом.................
        """
        response = self.authorized_user.get(reverse('post_edit', kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        form_fields = {'text': forms.fields.CharField, }
        for value, expect in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expect)

    def test_context_in_template_profile(self):
        """Шаблон profile сформирован с правильным контекстом...................
        """
        response = self.authorized_user.get(reverse('profile', kwargs={
            'username': self.user.username, }))
        profile = {'author': self.post.author}
        for value, expect in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expect)

        test_page = response.context['page'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_context_in_template_post(self):
        """Шаблон post сформирован с правильным контекстом......................
        """
        response = self.authorized_user.get(reverse('post', kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        profile = {'author': self.post.author, 'post': self.post}
        for value, expect in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expect)

    def test_post_not_in_wrong_group(self):
        """Проверка что post не попал ни в ту группу............................
        и попал в нужную"""
        cache.clear()
        Group.objects.create(title='new_group', slug='new_slug')
        response = self.authorized_user.get(reverse('group', kwargs={
            'slug': 'new_slug'}))
        group = response.context['group']
        post = group.posts.count()
        self.assertEqual(post, 0)
        self.assertEqual(len(response.context['page'].object_list), 0)
        response = self.authorized_user.get(reverse('index'))
        post = response.context['page'][0]
        group = post.group
        self.assertEqual(group, self.group)

    def test_wrong_uri_returns_404(self):
        """Проверка страницы 404................................................
        """
        response = self.authorized_user.get('chtoto/poshlo/ne.tak')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'misc/404.html')

    def test_wrong_uri_returns_500(self):
        """Проверка страницы 404................................................
        """
        response = self.authorized_user.get(reverse('page500'))
        self.assertTemplateUsed(response, 'misc/500.html')


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')
        for counts in range(POSTS_COUNT):
            cls.post = Post.objects.create(
                author=cls.user, text='Тестовый пост под номером {counts}',
                group=cls.group)
        cls.templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/group.html': reverse('group', kwargs={
                'slug': cls.group.slug}),
            'posts/profile.html': reverse('profile', kwargs={
                'username': cls.user.username})}

    def test_first_page_have_ten_posts(self):
        """Проверка первой страницы paginator должен показать 10 постов.........
        """
        cache.clear()
        for adress, reverse_name in self.templates_pages_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_user.get(reverse_name)
                self.assertEqual(len(response.context.get('page').object_list),
                                 PAGE_COUNT)

    def test_second_page_have_three_posts(self):
        """Проверка второй страницы paginator должен покажать 3 поста...........
        """
        for adress, reverse_name in self.templates_pages_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_user.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context.get('page').object_list),
                                 POSTS_COUNT - PAGE_COUNT)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')

    def test_cache_index(self):
        """Проверка что страница индекса работает с 20 секундным кешем..........
        """
        cache.clear()
        Post.objects.create(author=self.user, text='test cache text',
                            group=self.group)
        self.authorized_user.get(reverse('index'))
        response = self.authorized_user.get(reverse('index'))
        self.assertEqual(response.context, None)
        cache.clear()
        response = self.authorized_user.get(reverse('index'))
        self.assertNotEqual(response.context, None)
        self.assertEqual(response.context['page'][0].text, 'test cache text')


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')
        cls.follow_user = User.objects.create_user(username='TestAuthor')

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_user.force_login(self.follow_user)

    def test_follow(self):
        """Тест что подписка работает и фаловер добавляетя......................
        """
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.author, self.user)
        self.assertEqual(follow.user, self.follow_user)

    def test_unfollow(self):
        """Тест что фаловер может отписаться....................................
        """
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        self.authorized_user.get(reverse('profile_unfollow', kwargs={
            'username': self.user.username}))
        self.assertFalse(Follow.objects.exists())

    def test_follow_index(self):
        """Тест что пост появляется в ленте фаловера............................
        """
        Post.objects.create(author=self.user, text='test follow text',
                            group=self.group)
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        response = self.authorized_user.get(reverse('follow_index'))
        post = response.context['post']
        self.assertEqual(post.text, 'test follow text')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, self.group.id)

    def test_not_follow_index(self):
        """Тест что у не фаловера посты не появляются...........................
        """
        Post.objects.create(author=self.user, text='test follow text',
                            group=self.group)
        response = self.authorized_user.get(reverse('follow_index'))
        self.assertEqual(response.context['paginator'].count, 0)

    def test_following_self(self):
        """Тест что нельзя подписаться на самого себя...........................
        """
        self.assertEqual(Follow.objects.all().count(), 0)
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.follow_user.username}))
        self.assertEqual(Follow.objects.all().count(), 0)
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        self.assertEqual(Follow.objects.all().count(), 1)


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.comment_user = User.objects.create_user(username='TestCommentUser')
        cls.post = Post.objects.create(text='test text', author=cls.user)
        cls.url_comment = reverse('add_comment', kwargs={
            'username': cls.post.author.username, 'post_id': cls.post.id})

    def setUp(self):
        self.anonymous = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.comment_user)

    def test_comment_anonymous(self):
        """Тест что анонима редиректит на авторизацию...........................
        при попытки комментировать"""
        response = self.anonymous.get(self.url_comment)
        urls = '/auth/login/?next={}'.format(self.url_comment)
        self.assertRedirects(response, urls, status_code=HTTPStatus.FOUND)

    def test_comment_authorized(self):
        """Тест что авторизированный юзер может комментировать..................
        """
        response = self.authorized_user.post(self.url_comment, {
            'text': 'test comment'}, follow=True)
        self.assertContains(response, 'test comment')

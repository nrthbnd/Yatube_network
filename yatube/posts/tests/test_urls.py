from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.MAIN_PAGE = '/'
        cls.GROUP_LIST = f'/group/{PostURLTests.group.slug}/'
        cls.PROFILE = f'/profile/{PostURLTests.post.author}/'
        cls.POST_DETAIL = f'/posts/{PostURLTests.post.pk}/'
        cls.UNEXISTIING_PAGE = '/unexisting_page/'
        cls.URL_POST_CREATE = '/create/'
        cls.URL_REDIR_POST_CREATE = '/auth/login/?next=/create/'
        cls.URL_POST_EDIT = f'/posts/{PostURLTests.post.pk}/edit/'
        cls.URL_REDIR_POST_EDIT = (
            f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/')
        cls.URL_COMMENT_POST = f'/posts/{PostURLTests.post.pk}/comment/'
        cls.URL_REDIR_COMMENT_POST = (
            f'/auth/login/?next=/posts/{PostURLTests.post.pk}/comment/')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_exists_at_desired_location(self):
        """Страница ... доступна любому пользователю."""
        pages_url = {
            self.MAIN_PAGE: HTTPStatus.OK,
            self.GROUP_LIST: HTTPStatus.OK,
            self.PROFILE: HTTPStatus.OK,
            self.POST_DETAIL: HTTPStatus.OK,
            self.UNEXISTIING_PAGE: HTTPStatus.NOT_FOUND,
        }
        for address, http_status in pages_url.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_post_create_url_redirect_anonymous_on_login(self):
        """Страница create/ перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get(self.URL_POST_CREATE, follow=True)
        self.assertRedirects(response, self.URL_REDIR_POST_CREATE)

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница posts/<int:post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get(self.URL_POST_EDIT, follow=True)
        self.assertRedirects(response, self.URL_REDIR_POST_EDIT)

    def test_comment_post_url_redirect_anonymous_on_login(self):
        """Страница posts/<int:post_id>/comment/ перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get(self.URL_COMMENT_POST, follow=True)
        self.assertRedirects(response, self.URL_REDIR_COMMENT_POST)


class UrlTemplateCorrect(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.URL_MAIN_PAGE = '/'
        cls.URL_GROUP_LIST = f'/group/{UrlTemplateCorrect.group.slug}/'
        cls.URL_PROFILE = f'/profile/{UrlTemplateCorrect.post.author}/'
        cls.URL_POST_DETAIL = f'/posts/{UrlTemplateCorrect.post.pk}/'
        cls.URL_POST_EDIT = f'/posts/{UrlTemplateCorrect.post.pk}/edit/'
        cls.URL_POST_CREATE = '/create/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.URL_MAIN_PAGE: 'posts/index.html',
            self.URL_GROUP_LIST: 'posts/group_list.html',
            self.URL_PROFILE: 'posts/profile.html',
            self.URL_POST_DETAIL: 'posts/post_detail.html',
            self.URL_POST_EDIT: 'posts/create_post.html',
            self.URL_POST_CREATE: 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

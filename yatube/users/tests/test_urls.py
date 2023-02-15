from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import User

User = get_user_model()


class UserURLTests(TestCase):

    def setUp(self) -> None:
        self.guest_client = Client()

    def test_signup_url_exists_at_desired_location(self):
        """Страница auth/signup доступна всем пользователям."""
        response = self.guest_client.get('/auth/signup/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

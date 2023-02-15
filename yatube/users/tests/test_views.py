from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User

User = get_user_model()


class UserViewsTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_signup_page_uses_correct_template(self):
        """URL-адрес users:signup использует шаблон users/signup.html."""
        response = self.guest_client.get(reverse('users:signup'))
        self.assertTemplateUsed(response, 'users/signup.html')

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_post_have_correct_object_name(self):
        """Проверяем, что у постов корректно работает __str__."""
        post = self.post
        post_text = post.text[:15]
        self.assertEqual(post_text, str(post),
                         'Не крректно работает __str__ в models_post')

    def test_models_group_have_correct_object_name(self):
        """Проверяем, что у групп корректно работает __str__."""
        group = PostModelTest.group
        group_title = group.title
        self.assertEqual(group_title, str(group),
                         'Не крректно работает __str__ в models_group')

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value,
                    'verbose_name в полях не совпадает с ожидаемым.')

    def test_post_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value,
                    'help_text в полях не совпадает с ожидаемым.')

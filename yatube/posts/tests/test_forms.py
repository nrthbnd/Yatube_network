import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий',
        )
        cls.form = PostForm()
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{PostFormTests.post.pk}'})
        cls.URL_ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={'post_id': f'{PostFormTests.post.pk}'})
        cls.URL_POST_CREATE = reverse('posts:post_create')
        cls.URL_PROFILE = reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.post.author.username})
        cls.URL_POST_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostFormTests.post.pk})
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': PostFormTests.post.pk})
        cls.URL_LOGIN = reverse('users:login')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает новый пост в БД."""
        posts_count = Post.objects.count()
        old_ids = list(Post.objects.values_list('pk', flat=True))
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            self.URL_POST_CREATE,
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.exclude(pk__in=old_ids).first()
        self.assertRedirects(response, self.URL_PROFILE)
        self.assertEqual(Post.objects.count(), posts_count + 1,
                         'Кол-во постов должно увеличиться на 1.')
        self.assertEqual(new_post.text, form_data['text'],
                         'Некорректно создан новый пост (текст).')
        self.assertEqual(new_post.group.pk, form_data['group'],
                         'Некорректно создан новый пост (группа).')
        self.assertEqual(new_post.author.username, self.post.author.username,
                         'Некорректно создан новый пост (автор).')

    def test_create_post_with_picture(self):
        """Валидная форма создает новый пост с картинкой в БД."""
        post_count = Post.objects.count()
        picture = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='picture.gif',
            content=picture,
            content_type='image/gif'
        )
        old_ids = list(Post.objects.values_list('pk', flat=True))
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.URL_POST_CREATE,
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.exclude(pk__in=old_ids).first()
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1,
                         'Кол-во постов должно увеличиться на 1.')
        self.assertEqual(new_post.text, form_data['text'],
                         'Некорректно создан новый пост (текст).')
        self.assertEqual(new_post.group.pk, form_data['group'],
                         'Некорректно создан новый пост (группа).')
        self.assertEqual(new_post.author.username, self.post.author.username,
                         'Некорректно создан новый пост (автор).')
        self.assertEqual(
            new_post.image.name,
            'posts/' + str(form_data['image']),
            'Некорректно создан новый пост (картинка).')

    def test_post_edit(self):
        """Валидная форма изменяет существующую запись, не создавая новую."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст поста.',
            'group': PostFormTests.group.pk,
        }
        response = self.authorized_client.post(
            self.URL_POST_EDIT,
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        edited_post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, self.URL_POST_DETAIL)
        self.assertEqual(Post.objects.count(), posts_count,
                         'При редактировании поста кол-во постов не меняется.')
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'Ошибка при проверке статус-кода.')
        self.assertEqual(edited_post.text, form_data['text'],
                         'Некорректно откорректирован пост (текст).')
        self.assertEqual(edited_post.group.pk, form_data['group'],
                         'Некорректно откорректирован пост (группа).')
        self.assertEqual(self.user.username,
                         edited_post.author.username,
                         'Некорректно откорректирован пост (группа).')

    def test_not_authorized_client_cant_create_post(self):
        """Неавторизованный пользователь не может опубликовать пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            self.URL_POST_CREATE,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            self.URL_LOGIN + '?next=' + self.URL_POST_CREATE)
        self.assertEqual(Post.objects.count(), posts_count,
                         'Ошибка. Новый пост не должен создаваться.')

    def test_add_comment(self):
        """Валидная форма добавляет комментарий"""
        comments_count = Comment.objects.count()
        old_comments = list(Comment.objects.values_list('pk', flat=True))
        form_data = {
            'text': 'Тестовый комментарий',
            'post': self.post,
            'author': self.user,
        }
        response = self.authorized_client.post(
            self.URL_ADD_COMMENT,
            data=form_data,
            follow=True,
        )
        new_comment = Comment.objects.exclude(pk__in=old_comments).first()
        self.assertRedirects(
            response, self.URL_POST_DETAIL)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(
            new_comment.post, form_data['post'],
            'Некорректно создан новый комментарий (не тот пост).')
        self.assertEqual(
            new_comment.text, form_data['text'],
            'Некорректно создан новый комментарий (не тот текст).')
        self.assertEqual(
            new_comment.author.username, form_data['author'].username,
            'Некорректно создан новый комментарий (не тот автор).')

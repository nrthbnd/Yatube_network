from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
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
        cls.on_page = settings.AMOUNT_OF_POSTS

        cls.URL_MAIN_PAGE = reverse('posts:main_page')
        cls.URL_POST_CREATE = reverse('posts:post_create')
        cls.URL_GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': PostViewsTests.group.slug})
        cls.URL_PROFILE = reverse(
            'posts:profile',
            kwargs={'username': PostViewsTests.user.username})
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostViewsTests.post.pk})
        cls.URL_POST_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostViewsTests.post.pk})

        cls.post_with_image = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с картинкой',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.user1 = User.objects.create_user(username='First_user')
        self.user2 = User.objects.create_user(username='Second_user')
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-group')
        self.post = Post.objects.create(text='Тестовый пост',
                                        group=self.group,
                                        author=self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """Во view-функциях используются правильные html-шаблоны."""
        templates_pages_names = {
            self.URL_MAIN_PAGE: 'posts/index.html',
            self.URL_POST_CREATE: 'posts/create_post.html',
            self.URL_GROUP_LIST: 'posts/group_list.html',
            self.URL_PROFILE: 'posts/profile.html',
            self.URL_POST_EDIT: 'posts/create_post.html',
            self.URL_POST_DETAIL: 'posts/post_detail.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_main_page_page_shows_correct_context(self):
        """Шаблон main_page сформирован с правильным контекстом."""
        expected_context = (Post.objects.select_related('author').
                            order_by('-pub_date'))
        response = self.authorized_client.get(self.URL_MAIN_PAGE)
        self.assertEqual(
            response.context['page_obj'][:self.on_page],
            list(expected_context))

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author
        post_text = first_object.text
        post_group = first_object.group
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_group, self.group)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(self.URL_PROFILE))
        self.assertEqual(
            response.context.get('author').username,
            self.user.username)

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})))
        self.assertEqual(
            response.context.get('post').pk, self.post.pk)

    def test_post_create_page_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.URL_POST_CREATE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.URL_POST_EDIT)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_right(self):
        """При создании пост добавляется корректно."""
        response_main_page = self.authorized_client.get(self.URL_MAIN_PAGE)
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        response_profile = self.authorized_client.get(self.URL_PROFILE)

        main_page = response_main_page.context['page_obj'][0]
        group_list = response_group_list.context['page_obj'][0]
        profile = response_profile.context['page_obj'][0]

        self.assertEqual(self.post.pk, main_page.pk,
                         'Поста нет на главной странице.')
        self.assertEqual(self.post.pk, group_list.pk,
                         'Поста нет на странице группы.')
        self.assertEqual(self.post.pk, profile.pk,
                         'Поста нет в профиле пользователя.')

    def test_image_transfers_in_context(self):
        """При выводе поста с картинкой она передаётся в словаре context."""
        pages_addresses = (
            ('posts:main_page', None,),
            ('posts:group_list', (self.post_with_image.group.slug,)),
            ('posts:profile', (self.user.username,)),
        )
        post_with_image = Post.objects.get(pk=self.post_with_image.pk)
        for address, parameters in pages_addresses:
            response = self.authorized_client.get(
                reverse(address, args=parameters))
            with self.subTest(response=response):
                self.assertIn(
                    post_with_image,
                    response.context['page_obj'].object_list)
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post_with_image.pk,))
        )
        self.assertEqual(post_with_image, response.context['post'])

    def test_new_comment_create_correct_pages(self):
        """После успешной отправки комментарий появляется на странице поста"""
        response = self.authorized_client.get(self.URL_POST_DETAIL)
        self.assertEqual(response.context['comment'][0], self.comment)

    def test_main_page_cached(self):
        """Проверка кеширования страницы main_page."""
        test_post = Post.objects.create(
            text='Тестовый пост для тестирования кэша.',
            author=self.user,
        )
        response = self.authorized_client.get(self.URL_MAIN_PAGE)
        Post.objects.filter(pk=test_post.pk).delete()
        response_after_delete = self.authorized_client.get(self.URL_MAIN_PAGE)
        self.assertEqual(response.content, response_after_delete.content)

        cache.clear()

        response_after_cache_clear = self.authorized_client.get(
            self.URL_MAIN_PAGE)

        self.assertNotEqual(
            response.content,
            response_after_cache_clear.content
        )


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.NUMBER_OF_POSTS = 13
        cls.on_page = settings.AMOUNT_OF_POSTS
        cls.left_posts = cls.NUMBER_OF_POSTS % cls.on_page
        cls.error_1st_page = ('Ошибка: постов должно быть '
                              f'{cls.on_page}.')
        cls.error_2nd_page = ('Ошибка: постов должно быть '
                              f'{cls.left_posts}.')

        cls.user = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test_group',
            description='Тестовое описание',
        )
        number_of_posts = []
        for i in range(cls.NUMBER_OF_POSTS):
            number_of_posts.append(
                Post(
                    author=cls.user,
                    text=f'Тестовый пост № {i}',
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(number_of_posts)
        cls.count_post = Post.objects.count()

        cls.URL_MAIN_PAGE = reverse('posts:main_page')
        cls.URL_GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': f'{PaginatorViewsTests.group.slug}'})
        cls.URL_PROFILE = reverse(
            'posts:profile',
            kwargs={'username': f'{PaginatorViewsTests.user.username}'})

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """На первой странице отображается 10 постов."""
        response_main_page = self.authorized_client.get(
            reverse('posts:main_page'))
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))

        self.assertEqual(len(
            response_main_page.context['page_obj']),
            self.on_page,
            self.error_1st_page)
        self.assertEqual(len(
            response_group_list.context['page_obj']),
            self.on_page,
            self.error_1st_page)
        self.assertEqual(len(
            response_profile.context['page_obj']),
            self.on_page,
            self.error_1st_page)

    def test_second_page_contains_three_records(self):
        """На второй странице отображается 3 поста."""
        response_main_page = self.authorized_client.get(
            self.URL_MAIN_PAGE + '?page=2')
        response_group_list = self.authorized_client.get(
            self.URL_GROUP_LIST + '?page=2')
        response_profile = self.authorized_client.get(
            self.URL_PROFILE + '?page=2')

        self.assertEqual(len(
            response_main_page.context['page_obj']),
            self.left_posts,
            self.error_2nd_page)
        self.assertEqual(len(
            response_group_list.context['page_obj']),
            self.left_posts,
            self.error_2nd_page)
        self.assertEqual(len(
            response_profile.context['page_obj']),
            self.left_posts,
            self.error_2nd_page)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HasNoName')
        cls.foll_user = User.objects.create(username='Following_User')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user)
        cls.URL_POST_PROFILE_FOLLOW = reverse(
            'posts:profile_follow',
            kwargs={'username': FollowTests.foll_user.username})
        cls.URL_POST_PROFILE_UNFOLLOW = reverse(
            'posts:profile_unfollow',
            kwargs={'username': FollowTests.foll_user.username})
        cls.URL_FOLLOW_INDEX = reverse('posts:follow_index')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        follows_count = Follow.objects.count()
        self.authorized_client.get(self.URL_POST_PROFILE_FOLLOW)
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        follow_link = Follow.objects.filter(
            author=self.foll_user,
            user=self.user)
        self.assertEqual(len(follow_link), 1)
        self.assertEqual(follow_link[0].author, self.foll_user)
        self.assertEqual(follow_link[0].user, self.user)

    def test_unfollow(self):
        """Авторизованный пользователь может удалять
        пользователей из подписок."""
        Follow.objects.create(
            author=self.foll_user,
            user=self.user,
        )
        follows_count = Follow.objects.count()
        self.authorized_client.get(self.URL_POST_PROFILE_UNFOLLOW)
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_follower_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        Follow.objects.create(
            author=self.foll_user,
            user=self.user,
        )
        following_post = Post.objects.create(
            author=self.foll_user,
            text='Ты на меня подписан',
        )
        posts = self.authorized_client.get(
            self.URL_FOLLOW_INDEX).context.get('page_obj').object_list
        self.assertIn(following_post, posts)

    def test_not_follower_index(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        Follow.objects.create(
            author=self.user,
            user=self.foll_user,
        )
        not_following_post = Post.objects.create(
            author=self.user,
            text='Ты на меня подписан',
        )
        posts = self.authorized_client.get(
            self.URL_FOLLOW_INDEX).context.get('page_obj').object_list
        self.assertNotIn(not_following_post, posts)

    def test_follow_yourself(self):
        """Авторизованный пользователь не может подписаться на самого себя."""
        follows_count_1 = Follow.objects.filter(
            user=self.user,
            author=self.user,
        ).count()
        self.authorized_client.get(self.URL_POST_PROFILE_FOLLOW)
        follows_count_2 = Follow.objects.filter(
            user=self.user,
            author=self.user,
        ).count()
        self.assertEqual(follows_count_1, follows_count_2)

import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()

TEST_OF_POST = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.new_group = Group.objects.create(
            title='Новая группа',
            slug='slug_slug',
            description='Новое описание',
        )

        cls.new_post = Post.objects.create(
            author=cls.user,
            text='Новый пост',
            group=cls.new_group
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_follower = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.author)
        self.authorized_client_follower.force_login(self.follower)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.id, ViewsURLTests.post.id)
        self.assertEqual(first_object.author_id, ViewsURLTests.user.id)
        self.assertEqual(first_object.author, ViewsURLTests.user)
        self.assertEqual(first_object.text, ViewsURLTests.post.text)
        self.assertEqual(first_object.image, ViewsURLTests.post.image)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.assertEqual(response.context.get(
            'group').id, ViewsURLTests.group.id)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author_id, ViewsURLTests.user.id)
        self.assertEqual(first_object.author, ViewsURLTests.user)
        self.assertEqual(first_object.image, ViewsURLTests.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id':
                                                 self.post.id}))
        self.assertEqual(response.context.get(
            'post').id, ViewsURLTests.post.id)
        self.assertEqual(response.context.get(
            'post').text, ViewsURLTests.post.text)
        self.assertEqual(response.context.get(
            'post').author_id, ViewsURLTests.user.id)
        self.assertEqual(response.context.get(
            'post').author, ViewsURLTests.user)
        self.assertEqual(response.context.get(
            'post').group_id, ViewsURLTests.group.id)
        self.assertEqual(response.context.get(
            'post').group, ViewsURLTests.post.group)
        self.assertEqual(response.context.get(
            'post').image, ViewsURLTests.post.image)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_on_page_index_profile_group_list(self):
        """Пост появляется на index, group_list, profile."""
        templates_names = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.new_post.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )
        for reverse_name in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.new_post, response.context['page_obj'])

    def test_post_not_for_your_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        self.assertNotIn(self.new_post, response.context['page_obj'])

    def test_cache(self):
        """Проверка работы кэша."""
        response1 = self.client.get(reverse('posts:index'))
        Post.objects.create(text='Текст для проверки кэша', author=self.user)
        response2 = self.client.get(reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response3.content, response2.content)

    def test_authorized_author_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        response = self.authorized_client_follower.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.first().user, self.follower)
        self.assertEqual(Follow.objects.first().author, self.author)

    def test_authorized_author_profile_unfollow(self):
        """Авторизованный пользователь может и удалять
        пользователей из подписок."""
        response = self.authorized_client_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follower_author(self):
        """Появление новых постов у подписанных пользователей."""
        response1 = self.authorized_client_follower.post(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        Follow.objects.create(user=self.follower, author=self.user)
        response2 = self.authorized_client_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertTrue(Follow.objects.filter(user=self.follower,
                                              author=self.user).exists())
        self.assertNotEqual(response1, response2)


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        self.posts = Post.objects.bulk_create(
            [Post(
                author=self.user,
                text=f'Тестовый пост {i}',
                group=self.group)
                for i in range(TEST_OF_POST)]
        )

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10."""
        templates_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for reverse_name in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_NUM)

    def test_second_page_contains_three_records(self):
        """Количество постов на первой странице равно 3."""
        templates_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for reverse_name in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    TEST_OF_POST - settings.POSTS_NUM)

from math import ceil

from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, User, Comment, Follow
from ..constants import AMOUNT_PUBLICATION


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_POSTS = 15
        cls.NUMBER_OF_PAGES = ceil(cls.TEST_POSTS / AMOUNT_PUBLICATION)
        cls.PAGE_COEF = 1
        cls.user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        test_posts = []
        for number_of_posts in range(cls.TEST_POSTS):
            test_posts.append(Post(text=f'Текст поста № {number_of_posts}',
                                   group=cls.group,
                                   author=cls.user))
        Post.objects.bulk_create(test_posts)

    def test_paginator_post_in_page(self):
        """Проверка количества постов
         на первой и второй страницах index,
        group_list, profile.
        """
        pages_address = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}),
        )
        for address in pages_address:
            response_first_page = self.client.get(address)
            response_last_page = (
                self.client.get(
                    address + f'?page={self.NUMBER_OF_PAGES}')
            )
            with self.subTest(address=address):
                if self.TEST_POSTS > AMOUNT_PUBLICATION:
                    self.assertEqual(
                        len(response_first_page.context['page_obj']),
                        AMOUNT_PUBLICATION)
                else:
                    self.assertEqual(
                        len(response_first_page.context['page_obj']),
                        self.TEST_POSTS)
            with self.subTest(address=address):
                if (self.TEST_POSTS - (self.NUMBER_OF_PAGES - self.PAGE_COEF)
                        * AMOUNT_PUBLICATION == AMOUNT_PUBLICATION):
                    self.assertEqual(
                        len(response_last_page.context['page_obj']),
                        AMOUNT_PUBLICATION)
                else:
                    self.assertEqual(
                        len(response_last_page.context['page_obj']),
                        self.TEST_POSTS % AMOUNT_PUBLICATION
                    )


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Описание тестовой группы',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = User.objects.create_user(username='auth2')
        self.authorized_client.force_login(self.user)

        self.small_gif = (
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            group=self.group,
            author=self.user,
            image=self.uploaded
        )
        self.comment = Comment.objects.create(post_id=self.post.id,
                                              author=self.user,
                                              text='Тестовый коммент')

    def correct_context_for_pages(self, context):
        """Проверка контекста для главной страницы, групп и профайла."""
        post_object_fields = {
            context.text: self.post.text,
            context.author: self.user,
            context.group: self.group,
            context.group.id: self.group.id,
            context.image: self.post.image,
        }
        for item, expected in post_object_fields.items():
            with self.subTest(item=item):
                self.assertEqual(item, expected)

    def assert_post_response(self, response):
        """Проверяем context форм"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.correct_context_for_pages(response.context['page_obj'][0])

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        )
        self.assertEqual(response.context.get('group').title, self.group.title)
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.correct_context_for_pages(response.context['page_obj'][0])

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assert_post_response(response)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        self.assert_post_response(response)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text_0 = {
            response.context['post'].text: self.post.text,
            response.context['post'].group: self.group,
            response.context['post'].author: self.user,
            response.context['post'].group.id: self.post.group.id,
            response.context['post'].image: self.post.image,
            response.context['comments'][0].text: 'Тестовый коммент',
            response.context['comments'][0].author: self.user.username
        }

        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(response.context['author'], self.post.author)
        self.correct_context_for_pages(response.context['page_obj'][0])
        self.assertTrue(response.context.get('following'))

    def test_not_added_in_foreign_group(self):
        """Пост при создании не добавляется в чужую группу."""
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test_group2')
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug]))
        self.assertNotEqual(response.context['page_obj'][0], group2)

    def test_post_added_in_one_place_in_context(self):
        """Пост при создании добавляется в первое место в контексте."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug]))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_cache_context(self):
        """Проверка кэширования страницы index"""
        before_create_post = self.authorized_client.get(
            reverse('posts:index'))
        first_item_before = before_create_post.content
        Post.objects.create(
            author=self.user,
            text='Проверка кэша',
            group=self.group)
        after_create_post = self.authorized_client.get(reverse('posts:index'))
        first_item_after = after_create_post.content
        self.assertEqual(first_item_after, first_item_before)
        cache.clear()
        after_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_item_after, after_clear)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        self.post = Post.objects.create(text='Тестовый текст',
                                        group=self.group,
                                        author=self.user)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user1')
        cls.user2 = User.objects.create_user(username='user2')
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_follower_see_new_post(self):
        """Новая запись пользователя появляется в ленте тех,
         кто на него подписан"""
        new_post_follower = Post.objects.create(
            author=self.author,
            text='Текстовый текст',
        )
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_post = response.context['page_obj'].object_list[0]
        self.assertEqual(new_post_follower.text, new_post.text)

    def test_follow_another_user(self):
        """Авторизованный пользователь,
        может подписываться на других пользователей."""
        self.assertFalse(Follow.objects.filter(user=self.user,
                                               author=self.user2).exists())
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': self.user2}))

        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.user2).exists())
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow(self):
        """Авторизованный пользователь,
        может отписываться от других пользователей."""
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': self.user2}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           kwargs={'username': self.user2}))
        follow_count_after_unfollow = Follow.objects.count()
        self.assertEqual(Follow.objects.count(), follow_count_after_unfollow)

    def test_no_view_post_for_not_follower(self):
        """Пост не появляется в ленте подписок,
         если нет подписки на автора."""
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=self.user,
                              author=self.author)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)

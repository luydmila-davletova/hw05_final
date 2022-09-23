from django.test import TestCase

from ..models import Group, Post, User
from ..constants import LEN_TEXT


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
            text='Тестовое описание поста',
        )

    def test_models_have_correct_object_names(self):
        """Проверка длины __str__ post."""
        error_name = f"Вывод не имеет {LEN_TEXT} символов"
        self.assertEqual(self.post.__str__(),
                         self.post.text[0:LEN_TEXT],
                         error_name)

    def test_models_have_correct_title_names(self):
        """Метод ___str___ y group работает корректно."""
        group = PostModelTest.group
        title = group.__str__()
        self.assertEqual(title, group.title)

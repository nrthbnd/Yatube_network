from django.test import TestCase


class CoreViewsTests(TestCase):
    def test_404_page_uses_correct_tempate(self):
        """Несущестующая страница использует шаблон core/404.html."""
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')

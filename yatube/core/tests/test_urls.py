from django.test import TestCase, Client


class CustomURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_404(self):
        response = self.guest_client.get('/nonexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

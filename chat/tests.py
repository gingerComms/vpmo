from django.test import TestCase, Client
from django.shortcuts import reverse

from vpmoauth.models import MyUser

# Create your tests here.
class ChatTokenTestCase(TestCase):
    client = Client()

    def setUp(self):
        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)
        self.client.force_login(self.user)

    def test_token_generation(self):
        url = reverse("chat:twilio-token")

        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
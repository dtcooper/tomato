import json
import random

import base58

from django.test import TestCase
from django.urls import reverse

from .models import User


class ViewTests(TestCase):
    def post_json(self, url, data):
        return self.client.post(url, json.dumps(data), content_type="application/json")

    def test_access_token_view(self):
        url = reverse("access_token")
        user = User.objects.create_user(username="david", password="top-secret")
        response = self.post_json(url, {"username": "david", "password": "top-secret"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertDictContainsSubset({"status": "ok"}, data)
        self.assertNotIn("error", data)
        self.assertIn("access_token", data)

        access_token = data["access_token"]
        raw_access_token = base58.b58decode(access_token)
        self.assertEqual(len(raw_access_token), User.ACCESS_TOKEN_STRUCT.size)
        _, access_token_user_id, _ = User.ACCESS_TOKEN_STRUCT.unpack(raw_access_token)
        self.assertEqual(user.id, access_token_user_id)
        self.assertEqual(User.validate_access_token(access_token), user)

        response = self.post_json(url, {"username": "david", "password": "bad-password"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual({"status": "error", "error": "Invalid username and password combination."}, data)

        response = self.post_json(url, {"user": "david", "pass": "top-secret"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual({"status": "error", "error": "Please provide a username and password."}, data)

    def test_access_token(self):
        user = User.objects.create_user(username="david", password="top-secret")
        for bad_token_size in range(200):
            for _ in range(5):
                raw_bad_token = bytearray(random.randbytes(bad_token_size))
                if len(raw_bad_token) > User.ACCESS_TOKEN_SALT_LENGTH:
                    # Flip sign so user_id is always negative, so no possible way it can be a good token
                    raw_bad_token[User.ACCESS_TOKEN_SALT_LENGTH] |= 1 << 7

                bad_token = base58.b58encode(raw_bad_token)
                self.assertIsNone(User.validate_access_token(bad_token))

        access_token = user.generate_access_token()
        raw_access_token = base58.b58decode(access_token)
        self.assertEqual(len(raw_access_token), User.ACCESS_TOKEN_STRUCT.size)
        _, access_token_user_id, _ = User.ACCESS_TOKEN_STRUCT.unpack(raw_access_token)
        self.assertEqual(user.id, access_token_user_id)
        self.assertEqual(User.validate_access_token(access_token), user)
        reversed_access_token = access_token[::-1]
        self.assertIsNone(User.validate_access_token(reversed_access_token))

        user.set_password("new-secret")  # Setting password expires access token
        user.save()
        self.assertIsNone(User.validate_access_token(access_token))

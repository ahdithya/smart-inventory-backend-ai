from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Category


class CategoryPermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="ownerpass123",
            role=User.Role.OWNER,
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="staffpass123",
            role=User.Role.STAFF,
        )
        self.category = Category.objects.create(
            name="Minuman", description="Kategori minuman"
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # --- GET list (login required) ---
    def test_list_requires_authentication(self):
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_owner_can_see(self):
        self._auth(self.owner)
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["categories"]), 1)

    def test_list_staff_can_see(self):
        self._auth(self.staff)
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- GET detail (login required) ---
    def test_detail_requires_authentication(self):
        response = self.client.get(
            reverse("category-detail", args=[self.category.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_staff_can_see(self):
        self._auth(self.staff)
        response = self.client.get(
            reverse("category-detail", args=[self.category.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- POST (Owner only) ---
    def test_create_owner_allowed(self):
        self._auth(self.owner)
        response = self.client.post(
            reverse("category-list"), {"name": "Makanan", "description": "Kategori makanan"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name="Makanan").exists())

    def test_create_staff_forbidden(self):
        self._auth(self.staff)
        response = self.client.post(
            reverse("category-list"), {"name": "Makanan", "description": "Kategori makanan"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Category.objects.filter(name="Makanan").exists())

    def test_create_duplicate_name_rejected(self):
        self._auth(self.owner)
        response = self.client.post(
            reverse("category-list"), {"name": "Minuman", "description": "Duplikat"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- PUT (Owner only) ---
    def test_update_owner_allowed(self):
        self._auth(self.owner)
        response = self.client.put(
            reverse("category-detail", args=[self.category.pk]),
            {"name": "Minuman Dingin"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Minuman Dingin")

    def test_update_staff_forbidden(self):
        self._auth(self.staff)
        response = self.client.put(
            reverse("category-detail", args=[self.category.pk]),
            {"name": "Minuman Dingin"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- DELETE (Owner only) ---
    def test_delete_owner_allowed(self):
        self._auth(self.owner)
        response = self.client.delete(
            reverse("category-detail", args=[self.category.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_delete_staff_forbidden(self):
        self._auth(self.staff)
        response = self.client.delete(
            reverse("category-detail", args=[self.category.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from billing.models import Provider, Barrel

User = get_user_model()

class BarrelCreationTests(APITestCase):
    def setUp(self):
        # 1. Arrange: Creamos dos proveedores y un usuario para el A
        self.provider_a = Provider.objects.create(name="Provider A", tax_id="A123")
        self.provider_b = Provider.objects.create(name="Provider B", tax_id="B123")

        self.user_a = User.objects.create_user(
            username="usera", password="password123", provider=self.provider_a
        )
        self.client.force_authenticate(user=self.user_a)

    def test_create_barrel_forces_logged_in_user_provider(self):
        # 2. Act: Intentamos crear el barril asignándolo maliciosamente al Proveedor B
        payload = {
            "number": "BRL-001",
            "oil_type": "Olive",
            "liters": 150,
            "provider": self.provider_b.id  # ¡Trampa!
        }

        response = self.client.post("/api/barrels/", payload, format="json")

        # 3. Assert: Comprobamos que se crea correctamente (201)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Pero comprobamos en la base de datos que el servidor ignoró la trampa 
        # y le asignó el Proveedor A (el del usuario logueado)
        created_barrel = Barrel.objects.get(number="BRL-001")
        self.assertEqual(created_barrel.provider_id, self.provider_a.id)
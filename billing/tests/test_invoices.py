from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from billing.models import Provider, Barrel

User = get_user_model()

class ProviderAccessAndCalculationTests(APITestCase):
    def setUp(self):
        self.provider_a = Provider.objects.create(name="Provider A", tax_id="A123")
        self.provider_b = Provider.objects.create(name="Provider B", tax_id="B123")

        self.user_a = User.objects.create_user(
            username="usera", password="password", provider=self.provider_a
        )
        self.admin_user = User.objects.create_superuser(
            username="admin", password="password"
        )

        Barrel.objects.create(provider=self.provider_a, number="BRL-1", liters=100, billed=True)
        Barrel.objects.create(provider=self.provider_a, number="BRL-2", liters=50, billed=False)
        Barrel.objects.create(provider=self.provider_a, number="BRL-3", liters=20, billed=False)

    def test_admin_can_see_all_providers(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/providers/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
         
        # todos los proveedores que existan en la base de datos
        self.assertEqual(len(data), Provider.objects.count())

    def test_normal_user_sees_only_own_provider(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/providers/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.provider_a.id)

    def test_normal_user_cannot_access_other_provider_detail(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"/api/providers/{self.provider_b.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_provider_liters_calculations(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"/api/providers/{self.provider_a.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['billed_liters'], 100)
        self.assertEqual(response.data['liters_to_bill'], 70)
        
    def test_cannot_delete_billed_barrel(self):
        # 1. Arrange: Creamos un barril y lo marcamos como facturado
        billed_barrel = Barrel.objects.create(
            provider=self.provider_a, 
            number="BRL-BILLED", 
            liters=100, 
            billed=True
        )
        self.client.force_authenticate(user=self.user_a)

        # 2. Act: Intentamos borrarlo
        response = self.client.delete(f"/api/barrels/{billed_barrel.id}/")

        # 3. Assert: Debe devolver un 400 Bad Request y no borrarse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Comprobamos que el barril sigue existiendo en la base de datos
        self.assertTrue(Barrel.objects.filter(id=billed_barrel.id).exists())
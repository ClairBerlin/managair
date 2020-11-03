from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class OrganizationTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]
    url = ""

    def setUp(self):
        # tomTester is owner of the organization Test-Team with pk=1
        self.client.login(username="tomTester", password="test")
        self.url = reverse("organization-detail", kwargs={"pk": 1})

    def tearDown(self):
        self.client.logout()

    def test_get_organization(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test-Team")

    def test_patch_organization(self):
        request_data = {
            "data": {
                "type": format_resource_type("Organization"),
                "id": str(1),
                "attributes": {"description": "Test-Description"},
            }
        }
        response = self.client.patch(self.url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "Test-Description")

    def test_create_get_delete_organization(self):
        collection_url = reverse("organization-list")
        request_data = {
            "data": {
                "type": format_resource_type("Organization"),
                "attributes": {
                    "name": "Temp-Testers",
                    "description": "Vorübergehende Test-Organisation",
                },
            }
        }
        response = self.client.post(collection_url, data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Temp-Testers")
        self.assertEqual(
            response.data["description"], "Vorübergehende Test-Organisation"
        )
        # Fetch the organization resource just created.
        response_url = response.data["url"]
        response = self.client.get(response_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Temp-Testers")
        self.assertEqual(
            response.data["description"], "Vorübergehende Test-Organisation"
        )
        # Delete the organization.
        response = self.client.delete(response_url)
        self.assertEqual(response.status_code, 204)
        # Make sure it is gone.
        response = self.client.get(response_url)
        self.assertEqual(response.status_code, 404)

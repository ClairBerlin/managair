from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class OrganizationTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]
    url = ""

    def setUp(self):
        # tomTester is owner of the organization Test-Team with pk=1
        self.client.login(username="tomTester", password="test")
        self.detail_url = reverse("organization-detail", kwargs={"pk": 1})
        self.collection_url = reverse("organization-list")

    def tearDown(self):
        self.client.logout()

    def test_get_organizations(self):
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_organization(self):
        response = self.client.get(self.detail_url)
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
        response = self.client.patch(self.detail_url, data=request_data)
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
        response1 = self.client.post(collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["name"], "Temp-Testers")
        self.assertEqual(
            response1.data["description"], "Vorübergehende Test-Organisation"
        )
        # Fetch the organization resource just created.
        response_url = response1.data["url"]
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Temp-Testers")
        self.assertEqual(
            response2.data["description"], "Vorübergehende Test-Organisation"
        )
        # Delete the organization.
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_organization_users(self):
        url = reverse(
            "organization-related", kwargs={"pk": 1, "related_field": "users"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)

    def test_get_organization_user_relationships(self):
        url = reverse(
            "organization-relationships", kwargs={"pk": 1, "related_field": "users"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)

    def test_add_get_delete_user_relationship(self):
        url = reverse(
            "organization-relationships", kwargs={"pk": 1, "related_field": "users"}
        )
        request_data = {"data": [{"type": "User", "id": "4"}]}
        response1 = self.client.post(url, data=request_data)
        self.assertEqual(response1.status_code, 200)
        # See if the created relation is there.
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertIn({"type": "User", "id": "4"}, response2.data)
        # Delete the membership again.
        response3 = self.client.delete(url, data=request_data)
        self.assertEqual(response3.status_code, 200)

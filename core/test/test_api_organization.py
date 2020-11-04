from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class OrganizationTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # tomTester is owner of the organization Test-Team with pk=1
        self.client.login(username="tomTester", password="test")
        self.detail_url = reverse("organization-detail", kwargs={"pk": 1})
        self.collection_url = reverse("organization-list")

    def tearDown(self):
        self.client.logout()

    def test_get_organizations(self):
        """GET /organizations/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    # TODO: GET a specific organization via query-parameter.

    def test_get_organization(self):
        """GET /organizations/<organization_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test-Team")

    def test_patch_organization(self):
        """PATCH /organizations/<organization_id>/"""
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
        # POST /organizations/
        response1 = self.client.post(collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["name"], "Temp-Testers")
        self.assertEqual(
            response1.data["description"], "Vorübergehende Test-Organisation"
        )
        # Fetch the organization resource just created.
        # GET /organizations/<organization_id>/
        response_url = response1.data["url"]
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Temp-Testers")
        self.assertEqual(
            response2.data["description"], "Vorübergehende Test-Organisation"
        )
        # Delete the organization.
        # DELETE /organizations/<organization_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /organizations/<organization_id>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_organization_users(self):
        """GET /organizations/<organization_id>/users/"""
        url = reverse(
            "organization-related", kwargs={"pk": 1, "related_field": "users"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)

    def test_get_organization_user_relationships(self):
        """GET /organizations/<organization_id>/relationships/users/"""
        url = reverse(
            "organization-relationships", kwargs={"pk": 1, "related_field": "users"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)

    def test_add_get_delete_user_relationship(self):
        """ POST, GET, DELETE /organizatons/<organization_id>/relationships/users/"""
        url = reverse(
            "organization-relationships", kwargs={"pk": 1, "related_field": "users"}
        )
        request_data = {"data": [{"type": "User", "id": "4"}]}
        # POST /organizatons/<organization_id>/relationships/users/
        response1 = self.client.post(url, data=request_data)
        self.assertEqual(response1.status_code, 200)
        # See if the created relation is there.
        # GET /organizatons/<organization_id>/relationships/users/
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertIn({"type": "User", "id": "4"}, response2.data)
        # Delete the membership again.
        # DELETE /organizatons/<organization_id>/relationships/users/
        response3 = self.client.delete(url, data=request_data)
        self.assertEqual(response3.status_code, 200)
        # Ensure that the user is no longer a member of the organization.
        # GET /organizatons/<organization_id>/relationships/users/
        response4 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertNotIn({"type": "User", "id": "4"}, response4.data)

    def test_get_organization_nodes(self):
        """GET /organizations/<organization_id>/nodes/"""
        url = reverse(
            "organization-related", kwargs={"pk": 1, "related_field": "nodes"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_organization_sites(self):
        """GET /organizations/<organization_id>/sites/"""
        url = reverse(
            "organization-related", kwargs={"pk": 1, "related_field": "sites"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

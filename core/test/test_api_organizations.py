from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type
from .utils import TokenAuthMixin


class OrganizationTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # tomTester is owner of the organization Test-Team with pk=1
        self.auth_response, self.auth_token = self.authenticate(
            username="tomTester", password="test"
        )
        self.assertIsNotNone(self.auth_token)
        self.org_pk = 1
        self.detail_url = reverse("organization-detail", kwargs={"pk": self.org_pk})
        self.collection_url = reverse("organization-list")

    def tearDown(self):
        self.logout()

    def test_get_organizations(self):
        """GET /organizations/"""
        response = self.auth_get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 3)

    def test_get_organizations_public(self):
        """GET /organizations/ that are publicly visible."""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        # There is exactly one organization that has a public node installation
        self.assertEqual(len(response.data["results"]), 1)

    # TODO: GET a specific organization via query-parameter.

    def test_get_organization(self):
        """GET /organizations/<organization_id>/"""
        response = self.auth_get(self.detail_url)
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
        response = self.auth_patch(self.detail_url, data=request_data)
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
        response1 = self.auth_post(collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["name"], "Temp-Testers")
        self.assertEqual(
            response1.data["description"], "Vorübergehende Test-Organisation"
        )
        # Fetch the organization resource just created.
        # GET /organizations/<organization_id>/
        response_url = response1.data["url"]
        response2 = self.auth_get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Temp-Testers")
        self.assertEqual(
            response2.data["description"], "Vorübergehende Test-Organisation"
        )
        # Delete the organization.
        # DELETE /organizations/<organization_id>/
        response3 = self.auth_delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /organizations/<organization_id>/
        response4 = self.auth_get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_organization_users(self):
        """GET /organizations/<organization_pk>/users/"""
        url = reverse(
            "organization-related-users", kwargs={"organization_pk": self.org_pk}
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 4)

    def test_get_organization_memberships(self):
        """GET /organizations/<organization_pk>/memberships/"""
        url = reverse(
            "organization-related-memberships", kwargs={"organization_pk": self.org_pk}
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 4)

    def test_get_organization_user_relationships(self):
        """GET /organizations/<organization_pk/relationships/users/"""
        url = reverse(
            "organization-relationships",
            kwargs={"pk": self.org_pk, "related_field": "users"},
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)  # Indeed a flat response list.

    def test_add_get_delete_user_relationship(self):
        """ POST, GET, DELETE /organizatons/<organization_pk>/relationships/users/"""
        url = reverse(
            "organization-relationships",
            kwargs={"pk": self.org_pk, "related_field": "users"},
        )
        request_data = {"data": [{"type": "User", "id": "4"}]}
        # POST /organizatons/<organization_id>/relationships/users/
        response1 = self.auth_post(url, data=request_data)
        self.assertEqual(response1.status_code, 200)
        # See if the created relation is there.
        # GET /organizatons/<organization_id>/relationships/users/
        response2 = self.auth_get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertIn({"type": "User", "id": "4"}, response2.data)
        # Delete the membership again.
        # DELETE /organizatons/<organization_id>/relationships/users/
        response3 = self.auth_delete(url, data=request_data)
        self.assertEqual(response3.status_code, 200)
        # Ensure that the user is no longer a member of the organization.
        # GET /organizatons/<organization_id>/relationships/users/
        response4 = self.auth_get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertNotIn({"type": "User", "id": "4"}, response4.data)

    def test_get_organization_nodes(self):
        """GET /organizations/<organization_pk>/nodes/"""
        url = reverse(
            "organization-related-nodes", kwargs={"organization_pk": self.org_pk}
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_organization_sites(self):
        """GET /organizations/<organization_pk>/sites/"""
        url = reverse(
            "organization-related-sites", kwargs={"organization_pk": self.org_pk}
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_unauthorized_patch_no_member(self):
        """PATCH /organization/ where the user is not a member of."""
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbund (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Organization"),
                "id": str(1),
                "attributes": {"description": "Fake Description"},
            }
        }
        response = self.auth_patch(self.detail_url, data=request_data)
        # Expect a HTTP 404 error code, because the user should not have access to the
        # organization.
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_patch_no_owner(self):
        """PATCH /organization/ where the user is not an OWNER."""
        # User ingoInspekteur (pk=6) is INSPECTOR in Test-Team (pk=1).
        self.authenticate(username="ingoInspekteur", password="ingo")
        request_data = {
            "data": {
                "type": format_resource_type("Organization"),
                "id": str(1),
                "attributes": {"description": "Fake Description"},
            }
        }
        response = self.auth_patch(self.detail_url, data=request_data)
        # Expect a HTTP 403 error code, because the user can access the organization
        # but is not authorized to change it.
        self.assertEqual(response.status_code, 403)

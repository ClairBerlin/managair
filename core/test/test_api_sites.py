from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type
from .utils import TokenAuthMixin


class SitesTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        self.auth_response, self.auth_token = self.authenticate(
            username="veraVersuch", password="versuch"
        )
        self.assertIsNotNone(self.auth_token)
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.site_pk = 2
        self.detail_url = reverse("site-detail", kwargs={"pk": self.site_pk})
        self.collection_url = reverse("site-list")

    def tearDown(self):
        self.logout()

    def test_get_sites(self):
        """GET /sites/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_sites_public(self):
        """GET /sites/ available to a non-authenticated user."""
        # Make sure to not pass an authentication token.
        # self.client.defaults.pop("HTTP_AUTHORIZATION")
        self.logout()
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        # There is exactly one site that contains a public node installation in the
        # test data set.
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_sites_per_organization(self):
        """GET /sites/?filter[organization]=<organization_id>"""
        # Need a different user for this test case.
        # user priskaPrueferin is member in two organizations
        self.authenticate(username="priskaPrueferin", password="priska")
        response = self.client.get(self.collection_url, {"filter[organization]": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_site(self):
        """GET /sites/<site_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchs-Site")

    def test_patch_site(self):
        """PATCH /sites/<site_id>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Site"),
                "id": 2,
                "attributes": {
                    "name": "Versuchsort",
                    "description": "Ein nicht besonders besonderer Ort.",
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsort")
        self.assertEqual(
            response.data["description"], "Ein nicht besonders besonderer Ort."
        )

    def test_create_get_delete_site(self):
        request_data = {
            "data": {
                "type": format_resource_type("Site"),
                "attributes": {
                    "name": "Versuchsort 2",
                },
                "relationships": {
                    "address": {"data": {"type": "Address", "id": "2"}},
                    "operator": {"data": {"type": "Organization", "id": "2"}},
                },
            }
        }
        # POST /sites/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["name"], "Versuchsort 2")
        self.assertEqual(response1.data["address"]["id"], "2")
        self.assertEqual(response1.data["operator"]["id"], "2")
        # Fetch the site resource just created.
        response_url = response1.data["url"]
        # GET /sites/<site_id>/
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Versuchsort 2")
        self.assertEqual(response2.data["address"]["id"], "2")
        self.assertEqual(response2.data["operator"]["id"], "2")
        # Delete the site.
        # DELETE /site/<site_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /site/<site_id>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_site_rooms(self):
        """GET /sites/<site_pk>/rooms/"""
        url = reverse("site-related-rooms", kwargs={"site_pk": self.site_pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_unauthorized_create_no_member(self):
        """POST /sites/ for an organization where the user is not a member of."""
        request_data = {
            "data": {
                "type": format_resource_type("Site"),
                "attributes": {
                    "name": "Versuchsort 2",
                },
                "relationships": {
                    "address": {"data": {"type": "Address", "id": "2"}},
                    # The currently authenticated user VeraVersuch is not a member of
                    # the organization Test-Team with pk=1.
                    "operator": {"data": {"type": "Organization", "id": "1"}},
                },
            }
        }
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 403)

    def test_unauthorized_create_no_owner(self):
        """POST /sites/ for an organization where the user is not an OWNER."""
        # Need a different user for this test case.
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbung (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Site"),
                "attributes": {
                    "name": "Versuchsort 2",
                },
                "relationships": {
                    "address": {"data": {"type": "Address", "id": "2"}},
                    # The currently logged-in user horstHilfsarbeiter is not an OWNER
                    # of the organization Versuchsverbund with pk=2.
                    "operator": {"data": {"type": "Organization", "id": "2"}},
                },
            }
        }
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 403)

    def test_unauthorized_patch_no_member(self):
        """PATCH /sites/ of an organization where the user ist not a member of."""
        # Site 1 belongs to Test-Team, where the logged-in user is not a member of.
        site_id = 1
        detail_url = reverse("node-detail", kwargs={"pk": site_id})
        request_data = {
            "data": {
                "type": format_resource_type("Site"),
                "id": site_id,
                "attributes": {
                    "name": "Testort",
                    "description": "Ein Versuch der Unterwanderung",
                },
            }
        }
        response = self.client.patch(detail_url, data=request_data)
        # Expect a HTTP 404 error code, because the object to be patched should not be
        # accessible to the logged-in user.
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_patch_no_owner(self):
        """PATCH /sites/ of an organization where the user ist not an OWNER."""
        # Need a different user for this test case.
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbung (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Site"),
                "id": 2,
                "attributes": {
                    "name": "Versuchsort",
                    "description": "Ein Versuch der Unterwanderung",
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        # Expect a HTTP 403 error code, because the user has access to the Node but is
        # not sufficiently privileged to alter it.
        self.assertEqual(response.status_code, 403)

    # TODO: More Failure cases:
    # - Get Sites the user does not have access to.
    # - Add incompletely specified sites.
    # - PUT
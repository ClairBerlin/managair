from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class SitesTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        self.client.login(username="veraVersuch", password="versuch")
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("site-detail", kwargs={"pk": 2})
        self.collection_url = reverse("site-list")

    def tearDown(self):
        self.client.logout()

    def test_get_sites(self):
        """GET /sites/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    # TODO: GET a specific site via query-parameter.

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
                    "operated_by": {"data": {"type": "Organization", "id": "2"}},
                },
            }
        }
        # POST /sites/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["name"], "Versuchsort 2")
        self.assertEqual(response1.data["address"]["id"], "2")
        self.assertEqual(response1.data["operated_by"]["id"], "2")
        # Fetch the site resource just created.
        response_url = response1.data["url"]
        # GET /sites/<site_id>/
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Versuchsort 2")
        self.assertEqual(response2.data["address"]["id"], "2")
        self.assertEqual(response2.data["operated_by"]["id"], "2")
        # Delete the site.
        # DELETE /site/<site_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /site/<site_id>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_site_rooms(self):
        """GET /sites/<site_id>/rooms/"""
        url = reverse("site-related", kwargs={"pk": 2, "related_field": "rooms"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    # TODO: Failure cases:
    # - Sites the user does not have access to.
    # - Add incompletely specified sites.
    # - Illegal site updates.
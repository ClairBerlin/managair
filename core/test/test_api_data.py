from django.urls import reverse
from rest_framework.test import APITestCase
from .utils import TokenAuthMixin


class NodeTimeseriesTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json", "data-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        # Versuchs-Site has room Versuchsraum 1 (pk=3),
        # Prüf-Site has room Prüfstuge (pk=4).
        self.auth_response, self.auth_token = self.authenticate(
            username="veraVersuch", password="versuch"
        )
        self.assertIsNotNone(self.auth_token)
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("node-timeseries-detail", kwargs={"pk": self.node_id})
        self.collection_url = reverse("node-timeseries-list")

    def tearDown(self):
        self.logout()

    def test_get_node_timeseries_list(self):
        """GET /node-timeseries/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_get_node_timeseries_list_unauthenticated(self):
        """GET /node-timeseries/ without authentication."""
        self.client.defaults.pop("HTTP_AUTHORIZATION")
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 401)

    def test_get_node_timeseries(self):
        """GET /node-timeseries/<node_id>"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sample_count"], 589)
        self.assertEqual(len(response.data["samples"]), 589)

    def test_get_nodes_timeseries(self):
        """GET /nodes/<node_id>/timeseries/"""
        url = reverse(
            "node-related", kwargs={"pk": self.node_id, "related_field": "timeseries"}
        )
        response = self.client.get(url)
        self.assertEqual(response.data["sample_count"], 589)
        self.assertEqual(len(response.data["samples"]), 589)

    def test_get_nodes_timeseries_slice(self):
        """GET /nodes/<node_id>/timeseries/?filter[from]=<from_timestamp>&filter[to]=<to_timestamp>"""
        url = reverse(
            "node-related", kwargs={"pk": self.node_id, "related_field": "timeseries"}
        )
        response = self.client.get(
            url, data={"filter[from]": 1601725200, "filter[to]": 1601795400}
        )
        self.assertEqual(response.data["sample_count"], 39)
        self.assertEqual(len(response.data["samples"]), 39)
        self.assertEqual(response.data["from_timestamp_s"], 1601725200)
        self.assertEqual(response.data["to_timestamp_s"], 1601795400)

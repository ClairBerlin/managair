from django.urls import reverse
from rest_framework.test import APITestCase


class NodeTimeseriesTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json", "data-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        # Versuchs-Site has room Versuchsraum 1 (pk=3),
        # Prüf-Site has room Prüfstuge (pk=4).
        self.assertTrue(self.client.login(username="veraVersuch", password="versuch"))
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("node-timeseries-detail", kwargs={"pk": self.node_id})
        self.collection_url = reverse("node-timeseries-list")

    def tearDown(self):
        self.client.logout()

    def test_get_node_timeseries_list(self):
        """GET /node-timeseries/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_get_node_timeseries_list_unauthenticated(self):
        """GET /node-timeseries/ without authentication."""
        # Make sure we are not logged in.
        self.client.logout()
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 403)

    def test_get_node_timeseries(self):
        """GET /node-timeseries/<node_id>"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sample_count"], 589)
        self.assertEqual(len(response.data["samples"]), 589)

    def test_get_node_timeseries(self):
        """GET /nodes/<node_id>/timeseries/"""
        url = reverse(
            "node-related", kwargs={"pk": self.node_id, "related_field": "timeseries"}
        )
        response = self.client.get(url)
        self.assertEqual(response.data["sample_count"], 589)
        self.assertEqual(len(response.data["samples"]), 589)

    def test_get_node_timeseries_slice(self):
        """GET /nodes/<node_id>/timeseries/?filter[from]=<from_timestamp>&filter[to]=<to_timestamp>"""
        url = reverse(
            "node-related", kwargs={"pk": self.node_id, "related_field": "timeseries"}
        )
        response = self.client.get(
            url, {"filter[from]": 1601725200, "filter[to]": 1601795400}
        )
        self.assertEqual(response.data["sample_count"], 39)
        self.assertEqual(len(response.data["samples"]), 39)
        self.assertEqual(response.data["from_timestamp_s"], 1601725200)
        self.assertEqual(response.data["to_timestamp_s"], 1601795400)


class SamplesTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json", "data-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        self.client.login(username="veraVersuch", password="versuch")
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae).
        self.detail_url = reverse("sample-detail", kwargs={"pk": 1})
        self.collection_url = reverse("sample-list")

    def tearDown(self):
        self.client.logout()

    def test_get_samples_list(self):
        """GET /samples/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 100)  # Result is paged.
        self.assertEqual(response.data["meta"]["pagination"]["count"], 1554)

    def test_get_samples_list_unauthenticated(self):
        """GET /samples/ without authentication."""
        # Make sure we are not logged in.
        self.client.logout()
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 403)

    def test_get_sample_per_node(self):
        """GET /samples/?filter[node]=<node_id>"""
        response = self.client.get(self.collection_url, {"filter[node]": self.node_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 100)  # Result is paged.
        self.assertEqual(response.data["meta"]["pagination"]["count"], 589)

    def test_get_sample_slice_per_node(self):
        """GET /samples/?filter[node]=<node_id>&filter[from]=<from_timestamp&filter[to]=<to_timestamp"""
        response = self.client.get(
            self.collection_url,
            {
                "filter[node]": self.node_id,
                "filter[from]": 1601725200,
                "filter[to]": 1601795400,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 39)
        self.assertEqual(response.data["meta"]["pagination"]["count"], 39)

    # TODO: test query parameters and paging

    def test_get_sample(self):
        """GET /samples/<sample_id>"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timestamp_s"], 1577880000)

    def test_get_node_sampless(self):
        """GET /nodes/<node_id>/samples/"""
        url = reverse(
            "node-related", kwargs={"pk": self.node_id, "related_field": "samples"}
        )
        response = self.client.get(url)
        self.assertEqual(len(response.data["results"]), 589)
        self.assertEqual(response.data["meta"]["pagination"]["count"], 589)

    # TODO: test query parameters.
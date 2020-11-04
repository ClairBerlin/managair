from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class NodeTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]
    url = ""
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        self.client.login(username="veraVersuch", password="versuch")
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("node-detail", kwargs={"pk": self.node_id})
        self.collection_url = reverse("node-list")

    def tearDown(self):
        self.client.logout()

    def test_get_nodes(self):
        """GET /nodes/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    # TODO: GET a specific node via query-parameter.

    def test_get_node(self):
        """GET /node/<node_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["alias"], "Clairchen Schwarz")

    def test_patch_node(self):
        """PATCH /node/<node_id>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": self.node_id,
                "attributes": {
                    "device_id": "003CB7EA62A7DCBB",
                    "alias": "Clairchen Black",
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["alias"], "Clairchen Black")

    def test_create_get_delete_node(self):
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": "0094826d4b122b94d16caf86a16f9cc3",
                "attributes": {
                    "device_id": "fefffffffdff0000",
                    "alias": "Test Node",
                },
                "relationships": {
                    "protocol": {"data": {"type": "NodeProtocol", "id": "1"}},
                    "model": {"data": {"type": "NodeModel", "id": "1"}},
                    "owner": {"data": {"type": "Organization", "id": "2"}},
                },
            }
        }
        # POST /nodes/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["device_id"], "fefffffffdff0000")
        self.assertEqual(response1.data["alias"], "Test Node")
        # Fetch the node resource just created.
        response_url = response1.data["url"]
        # GET /nodes/<node_id/
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["device_id"], "fefffffffdff0000")
        self.assertEqual(response2.data["alias"], "Test Node")
        # Delete the node.
        # DELETE /node/<node_id/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /node/<node_id>
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_node_installations(self):
        """GET /nodes/<node_id>/installations/"""
        url = reverse(
            "node-related",
            kwargs={"pk": self.node_id, "related_field": "installations"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


    # TODO: Failure cases:
    # - Nodes the user does not have access to.
    # - Add incompletely specified nodes.
    # - Illegal node updates.

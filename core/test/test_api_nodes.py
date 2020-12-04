from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class NodeTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json", "data-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        self.assertTrue(self.client.login(username="veraVersuch", password="versuch"))
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

    def test_get_nodes_unauthenticated(self):
        """GET /nodes/ without authentication."""
        # Make sure we are not logged in.
        self.client.logout()
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 403)

    def test_get_nodes_per_organization(self):
        """GET /nodes/?filter[organization]=<organization_id>"""
        # Need a different user for this test case.
        self.client.logout()
        # user priskaPrueferin is member in two organizations
        self.client.login(username="priskaPrueferin", password="priska")
        response = self.client.get(self.collection_url, {"filter[organization]": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_node(self):
        """GET /node/<node_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["alias"], "Clairchen Schwarz")
        # Ensure that no timeseries is returned if we do not query for it.
        self.assertFalse("timeseries" in response.data)

    def test_get_node_with_timeseries(self):
        """GET /node/<node_id>?include_timeseries=True"""
        response = self.client.get(self.detail_url, {"include_timeseries": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["alias"], "Clairchen Schwarz")
        self.assertEqual(len(response.data["timeseries"]), 589)

    def test_patch_node(self):
        """PATCH /node/<node_id>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": self.node_id,
                "attributes": {
                    "eui64": "003CB7EA62A7DCBB",
                    "alias": "Clairchen Black",
                    "description": "This node belongs to the international node testing society."
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
                    "eui64": "fefffffffdff0000",
                    "alias": "Test Node",
                    "description": "What a node!"
                },
                "relationships": {
                    "protocol": {"data": {"type": "Protocol", "id": "1"}},
                    "model": {"data": {"type": "Model", "id": "1"}},
                    "owner": {"data": {"type": "Organization", "id": "2"}},
                },
            }
        }
        # POST /nodes/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["eui64"], "fefffffffdff0000")
        self.assertEqual(response1.data["alias"], "Test Node")
        # Fetch the node resource just created.
        response_url = response1.data["url"]
        # GET /nodes/<node_id>/
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["eui64"], "fefffffffdff0000")
        self.assertEqual(response2.data["alias"], "Test Node")
        # Delete the node.
        # DELETE /node/<node_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /node/<node_id>/
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

    def test_unauthorized_create_no_member(self):
        """POST /nodes/ for an organization the user ist not a member of."""
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": "0094826d4b122b94d16caf86a16f9cc3",
                "attributes": {
                    "eui64": "fefffffffdff0000",
                    "alias": "Test Node",
                },
                "relationships": {
                    "protocol": {"data": {"type": "Protocol", "id": "1"}},
                    "model": {"data": {"type": "Model", "id": "1"}},
                    # The currently logged-in user VeraVersuch is not a member of the
                    # # organization Test-Team with pk=1.
                    "owner": {"data": {"type": "Organization", "id": "1"}},
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_create_no_owner(self):
        """POST /nodes/ for an organization where the user is not an OWNER."""
        # Need a different user for this test case.
        self.client.logout()
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbund (pk=2).
        self.client.login(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": "0094826d4b122b94d16caf86a16f9cc3",
                "attributes": {
                    "eui64": "fefffffffdff0000",
                    "alias": "Test Node",
                },
                "relationships": {
                    "protocol": {"data": {"type": "Protocol", "id": "1"}},
                    "model": {"data": {"type": "Model", "id": "1"}},
                    # The currently logged-in user horstHilfsarbeiter is not an OWNER
                    # of the organization Versuchsverbund with pk=2.
                    "owner": {"data": {"type": "Organization", "id": "2"}},
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_patch_no_member(self):
        """PATCH /nodes/ of an organization of which the use ist not a member."""
        node_id = "c727b2f8-8377-d4cb-0e95-ac03200b8c93"
        node_eui = "9876B600001193E0"
        detail_url = reverse("node-detail", kwargs={"pk": node_id})
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": node_id,
                "attributes": {
                    "eui64": node_eui,
                    "alias": "Evil new alias",
                },
            }
        }
        response = self.client.patch(detail_url, data=request_data)
        # Expect a HTTP 404 error code, because the object to be patched should not be
        # accessible to the logged-in user.
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_patch_no_owner(self):
        """PATCH /nodes/ of an organization where the user ist not an OWNER."""
        # Need a different user for this test case.
        self.client.logout()
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbund (pk=2).
        self.client.login(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Node"),
                "id": self.node_id,
                "attributes": {
                    "eui64": "003CB7EA62A7DCBB",
                    "alias": "Evil new alias",
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        # Expect a HTTP 403 error code, because the user has access to the Node but is
        # not sufficiently privileged to alter it.
        self.assertEqual(response.status_code, 403)

    # TODO: More Failure cases:
    # - Add incompletely specified nodes.
    # - PUT
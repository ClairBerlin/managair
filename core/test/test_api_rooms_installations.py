from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class RoomsTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        # Versuchs-Site has room Versuchsraum 1 (pk=3),
        # Prüf-Site has room Prüfstuge (pk=4).
        self.client.login(username="veraVersuch", password="versuch")
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("room-detail", kwargs={"pk": 3})
        self.collection_url = reverse("room-list")

    def tearDown(self):
        self.client.logout()

    def test_get_rooms(self):
        """GET /rooms/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    # TODO: GET a specific room via query-parameter.

    def test_get_room(self):
        """GET /rooms/<room_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsraum 1")
        self.assertEqual(response.data["max_occupancy"], 17)

    def test_patch_room(self):
        """PATCH /rooms/<room_id>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Room"),
                "id": 3,
                "attributes": {
                    "description": "Ein Raum für Versuche.",
                    "height_m": "2.7",
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsraum 1")
        self.assertEqual(response.data["description"], "Ein Raum für Versuche.")
        self.assertEqual(response.data["height_m"], "2.7")

    def test_create_get_delete_room(self):
        request_data = {
            "data": {
                "type": format_resource_type("Room"),
                "attributes": {
                    "name": "Räumchen",
                    "description": "Nur zum Test",
                    "size_sqm": "5",
                    "height_m": "2.6",
                    "max_occupancy": 1,
                },
                "relationships": {
                    "site": {"data": {"type": "Site", "id": "3"}},
                },
            }
        }
        # POST /rooms/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["name"], "Räumchen")
        self.assertEqual(response1.data["description"], "Nur zum Test")
        self.assertEqual(response1.data["size_sqm"], "5.0")
        self.assertEqual(response1.data["height_m"], "2.6")
        self.assertEqual(response1.data["max_occupancy"], 1)
        self.assertEqual(response1.data["site"]["id"], "3")
        # Fetch the room resource just created.
        response_url = response1.data["url"]
        # GET /rooms/<room_id/>
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Räumchen")
        self.assertEqual(response2.data["description"], "Nur zum Test")
        self.assertEqual(response2.data["size_sqm"], "5.0")
        self.assertEqual(response2.data["height_m"], "2.6")
        self.assertEqual(response2.data["max_occupancy"], 1)
        self.assertEqual(response2.data["site"]["id"], "3")
        # Delete the room.
        # DELETE /room/<room_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /room/<room_id>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_room_installations(self):
        """GET /rooms/<room_id>/installations/"""
        url = reverse(
            "room-related", kwargs={"pk": 3, "related_field": "installations"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class InstallationsTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        # Versuchs-Site has room Versuchsraum 1 (pk=3),
        # Prüf-Site has room Prüfstuge (pk=4).
        self.client.login(username="veraVersuch", password="versuch")
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("installation-detail", kwargs={"pk": 2})
        self.collection_url = reverse("installation-list")

    def tearDown(self):
        self.client.logout()

    def test_get_installations(self):
        """GET /installations/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    # TODO: GET with various filter options.

    def test_get_installation(self):
        """GET /installations/<installation_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["from_timestamp_s"], 1601510400)

    def test_patch_installation(self):
        """PATCH /installations/<installation_id>/"""
        request_data = {
            "data": {
                "type": format_resource_type("RoomNodeInstallation"),
                "id": 2,
                "attributes": {"from_timestamp_s": 1601510000},  # Predate
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["from_timestamp_s"], 1601510000)

    # TODO: Test illegal time-slice overlaps

    def test_create_get_delete_installation(self):
        request_data = {
            "data": {
                "type": format_resource_type("RoomNodeInstallation"),
                "attributes": {
                    "from_timestamp_s": 1601500000,
                    "to_timestamp_s": 2147483647,
                    "description": "Testinstallation",
                },
                "relationships": {
                    # Install the ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee) in Prüfstube (id=4).
                    "node": {
                        "data": {
                            "type": format_resource_type("Node"),
                            "id": "9d02faee-4260-1377-22ec-936428b572ee",
                        }
                    },
                    "room": {
                        "data": {
                            "type": format_resource_type("Room"),
                            "id": "4",
                        }
                    },
                },
            }
        }
        # POST /memberships/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["from_timestamp_s"], 1601500000)
        self.assertEqual(
            response1.data["node"]["id"], "9d02faee-4260-1377-22ec-936428b572ee"
        )
        self.assertEqual(response1.data["room"]["id"], "4")
        # Fetch the installation resource just created.
        response_url = response1.data["url"]
        # GET /installations/<installation_id/>
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["from_timestamp_s"], 1601500000)
        self.assertEqual(
            response2.data["node"]["id"], "9d02faee-4260-1377-22ec-936428b572ee"
        )
        self.assertEqual(response2.data["room"]["id"], "4")
        # Delete the installation.
        # DELETE /installations/<installation_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /installations/<installation_id>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_installation_room(self):
        """GET /installations/<installations_id>/room/"""
        url = reverse("installation-related", kwargs={"pk": 2, "related_field": "room"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsraum 1")

    def test_get_installation_node(self):
        """GET /installations/<installations_id>/node/"""
        url = reverse("installation-related", kwargs={"pk": 2, "related_field": "node"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], "3b95a1b2-74e7-9e98-52c4-4acae441f0ae")

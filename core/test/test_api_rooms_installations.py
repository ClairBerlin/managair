from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type
from .utils import TokenAuthMixin


class RoomsTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Versuchserbund commands the sites Versuchs-Site (pk=2) and Prüf-Site (pk=3).
        # Versuchs-Site has room Versuchsraum 1 (pk=3),
        # Prüf-Site has room Prüfstuge (pk=4).
        self.auth_response, self.auth_token = self.authenticate(
            username="veraVersuch", password="versuch"
        )
        self.assertIsNotNone(self.auth_token)
        # Versuchsverbund owns Versuchsraum 1 with pk=3
        self.room_pk = 3
        self.detail_url = reverse("room-detail", kwargs={"pk": self.room_pk})
        self.collection_url = reverse("room-list")

    def tearDown(self):
        self.logout()

    def test_get_rooms(self):
        """GET /rooms/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_rooms_public(self):
        """GET /rooms/ without being logged-in"""
        # Make sure to not provide an authentication token.
        self.client.defaults.pop("HTTP_AUTHORIZATION")
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        # There is one room in the test data set that contains a public installation.
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_rooms_per_organization(self):
        """GET /rooms/?filter[organization]=<organization_id>"""
        # Need a different user for this test case.
        # user priskaPrueferin is member in two organizations
        self.authenticate(username="priskaPrueferin", password="priska")
        response = self.client.get(self.collection_url, {"filter[organization]": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_rooms_per_site(self):
        """GET /rooms/?filter[site]=<site_id>"""
        response = self.client.get(self.collection_url, {"filter[site]": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_room(self):
        """GET /rooms/<room_pk>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsraum 1")
        self.assertEqual(response.data["max_occupancy"], 17)

    def test_patch_room(self):
        """PATCH /rooms/<room_pk>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Room"),
                "id": self.room_pk,
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
                    "site": {"data": {"type": "Site", "id": self.room_pk}},
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
        # GET /rooms/<room_pk/>
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["name"], "Räumchen")
        self.assertEqual(response2.data["description"], "Nur zum Test")
        self.assertEqual(response2.data["size_sqm"], "5.0")
        self.assertEqual(response2.data["height_m"], "2.6")
        self.assertEqual(response2.data["max_occupancy"], 1)
        self.assertEqual(response2.data["site"]["id"], "3")
        # Delete the room.
        # DELETE /room/<room_pk>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /room/<room_pk>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_room_installations(self):
        """GET /rooms/<room_pk>/installations/"""
        url = reverse("room-related-installations", kwargs={"room_pk": self.room_pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_unauthorized_create_no_member(self):
        """POST /rooms/ for an organization the user ist not a member of."""
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
                    # The currently authenticated user VeraVersuch is not a member of
                    # the organization Test-Team with Site Test-Site (pk=1).
                    "site": {"data": {"type": "Site", "id": "1"}},
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_create_no_owner(self):
        """POST /rooms/ for an organization where the user is not an OWNER."""
        # Need a different user for this test case.
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbung (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
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
                    # The currently authenticated user horstHilfsarbeiter is not an
                    # OWNER of the organization Versuchsverbund with Versuchs-Site
                    # (pk=2).
                    "site": {"data": {"type": "Site", "id": "2"}},
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_patch_no_member(self):
        """PATCH /rooms/ of an organization of which the use ist not a member."""
        room_pk = 1  # Testraum 1 belongs to Organization Test-Team.
        detail_url = reverse("room-detail", kwargs={"pk": room_pk})
        request_data = {
            "data": {
                "type": format_resource_type("Room"),
                "id": room_pk,
                "attributes": {
                    "description": "Ein Raum für Versuche.",
                    "height_m": "2.7",
                },
            }
        }
        response = self.client.patch(detail_url, data=request_data)
        # Expect a HTTP 404 error code, because the object to be patched should not be
        # accessible to the logged-in user.
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_patch_no_owner(self):
        """PATCH /rooms/ of an organization where the user ist not an OWNER."""
        # Need a different user for this test case.
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbung (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Room"),
                "id": self.room_pk,
                "attributes": {
                    "description": "Ein Raum für Versuche.",
                    "height_m": "2.7",
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        # Expect a HTTP 403 error code, because the user has access to the Node but is
        # not sufficiently privileged to alter it.
        self.assertEqual(response.status_code, 403)


class InstallationsTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json", "data-fixtures.json"]
    node_id = "3b95a1b2-74e7-9e98-52c4-4acae441f0ae"  # Clairchen Schwarz
    node2_id = "9d02faee-4260-1377-22ec-936428b572ee"  # ERS Test-Node
    room_pk = 4  # Prüfstube
    inst_pk = 2

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
        self.detail_url = reverse("installation-detail", kwargs={"pk": self.inst_pk})
        self.collection_url = reverse("installation-list")

    def tearDown(self):
        self.logout()

    def test_get_installations(self):
        """GET /installations/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        # Ensure that no timeseries is returned if we do not query for it.
        self.assertFalse("timeseries" in response.data)

    def test_get_installations_public(self):
        """ GET /installations/ without authentication."""
        # Make sure to not provide an authentication token.
        self.client.defaults.pop("HTTP_AUTHORIZATION")
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        # There is exactly one public node installation in the test data.
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_installations_per_organization(self):
        """GET /installations/?filter[organization]=<organization_id>"""
        # Need a different user for this test case.
        # user priskaPrueferin is member in two organizations
        self.authenticate(username="priskaPrueferin", password="priska")
        response = self.client.get(self.collection_url, {"filter[organization]": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_installations_per_site(self):
        """GET /installations/?filter[site]=<site_id>"""
        response = self.client.get(self.collection_url, {"filter[site]": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["from_timestamp_s"], 1602720001)

    def test_get_installations_per_room(self):
        """GET /installations/?filter[room]=<room_pk>"""
        response = self.client.get(self.collection_url, {"filter[room]": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["from_timestamp_s"], 1601510400)

    def test_get_installations_per_node(self):
        """GET /installations/?filter[node]=<node_id>"""
        response = self.client.get(self.collection_url, {"filter[node]": self.node_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_installation(self):
        """GET /installations/<installation_pk>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["from_timestamp_s"], 1601510400)

    def test_get_installation_with_timeseries(self):
        """GET /installations/<installation_pk>/?include_timeseries=true"""
        response = self.client.get(self.detail_url, {"include_timeseries": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["timeseries"]), 468)

    def test_get_installation_with_timeseries_slice(self):
        """GET /installations/<installation_pk>/?include_timeseries=true&filter[from]=1601675365&filter[to]=1601738613"""
        response = self.client.get(
            self.detail_url,
            {
                "include_timeseries": True,
                "filter[from]": 1601675365,
                "filter[to]": 1601738613,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["timeseries"]), 71)

    def test_patch_installation(self):
        """PATCH /installations/<installation_pk>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "id": self.inst_pk,
                "attributes": {"from_timestamp_s": 1601510000, "is_public": True},
                "relationships": {
                    # Node and room must always be provided, to make sure owners match.
                    "node": {
                        "data": {
                            "type": format_resource_type("Node"),
                            "id": self.node_id,
                        }
                    },
                    "room": {
                        "data": {
                            "type": format_resource_type("Room"),
                            "id": 3,
                        }
                    },
                },
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["from_timestamp_s"], 1601510000)
        self.assertEqual(response.data["is_public"], True)

    # TODO: Test illegal time-slice overlaps

    def test_create_get_delete_installation(self):
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "attributes": {
                    "from_timestamp_s": 1601500000,
                    # Leave end timestamp open.
                    "description": "Testinstallation",
                    "is_public": False,
                },
                "relationships": {
                    # Install the ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee) in Prüfstube (id=4).
                    "node": {
                        "data": {
                            "type": format_resource_type("Node"),
                            "id": self.node2_id,
                        }
                    },
                    "room": {
                        "data": {
                            "type": format_resource_type("Room"),
                            "id": self.room_pk,
                        }
                    },
                },
            }
        }
        # POST /memberships/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["from_timestamp_s"], 1601500000)
        self.assertEqual(response1.data["to_timestamp_s"], 2147483647)
        self.assertEqual(
            response1.data["node"]["id"], "9d02faee-4260-1377-22ec-936428b572ee"
        )
        self.assertEqual(response1.data["room"]["id"], "4")
        # Fetch the installation resource just created.
        response_url = response1.data["url"]
        # GET /installations/<installation_pk/>
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["from_timestamp_s"], 1601500000)
        self.assertEqual(response2.data["node"]["id"], self.node2_id)
        self.assertEqual(response2.data["room"]["id"], "4")
        # Delete the installation.
        # DELETE /installations/<installation_pk>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /installations/<installation_pk>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_node_room_owner_mismatch(self):
        """POST /installations/ where the owner of the room and the node differ."""
        # Clairchen Rot belongs to Test-Team
        incorrect_node_id = "c727b2f8-8377-d4cb-0e95-ac03200b8c93"
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "attributes": {
                    "from_timestamp_s": 1601500000,
                    "to_timestamp_s": 2147483647,
                    "description": "Testinstallation",
                    "is_public": True,
                },
                "relationships": {
                    # Try to install Clairchen Rot in Prüfstube (id=4).
                    "node": {
                        "data": {
                            "type": format_resource_type("Node"),
                            "id": incorrect_node_id,
                        }
                    },
                    "room": {
                        "data": {
                            "type": format_resource_type("Room"),
                            "id": self.room_pk,
                        }
                    },
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        # Expect a HTTP 400 (Bad Request) error code, because the request data is
        # inconsistent.
        self.assertEqual(response.status_code, 400)

    def test_get_installation_room(self):
        """GET /installations/<installation_pk>/room/"""
        url = reverse(
            "installation-related", kwargs={"pk": self.inst_pk, "related_field": "room"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsraum 1")

    def test_get_installation_node(self):
        """GET /installations/<installation_pk>/node/"""
        url = reverse(
            "installation-related-node", kwargs={"installation_pk": self.inst_pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.node_id)

    def test_unauthorized_create_no_member(self):
        """POST /installations/ for an organization the user ist not a member of."""
        node_id = "c727b2f8-8377-d4cb-0e95-ac03200b8c93"
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "attributes": {
                    "from_timestamp_s": 1601500000,
                    "to_timestamp_s": 2147483647,
                    "description": "Testinstallation",
                    "is_public": True,
                },
                "relationships": {
                    # Install Clairchen Rot in Testraum 1 (pk=1).
                    # The currently authenticated user VeraVersuch is not a member of
                    # the organization that owns Testraum 1 and Clairchen Rot.
                    "node": {
                        "data": {
                            "type": format_resource_type("Node"),
                            "id": node_id,
                        }
                    },
                    "room": {
                        "data": {
                            "type": format_resource_type("Room"),
                            "id": 1,
                        }
                    },
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_create_no_owner(self):
        """POST /installations/ for an organization where the user is not an OWNER."""
        # Need a different user for this test case.
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbung (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "attributes": {
                    "from_timestamp_s": 1601500000,
                    "to_timestamp_s": 2147483647,
                    "description": "Testinstallation",
                    "is_public": False,
                },
                "relationships": {
                    # Install the ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee) in Prüfstube (id=4).
                    "node": {
                        "data": {
                            "type": format_resource_type("Node"),
                            "id": self.node2_id,
                        }
                    },
                    "room": {
                        "data": {
                            "type": format_resource_type("Room"),
                            "id": self.room_pk,
                        }
                    },
                },
            }
        }
        response = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_patch_no_member(self):
        """PATCH /installations/ of an organization of which the use ist not a member."""
        installation_id = 1  # Installation of Clairchen Rot in Testraum 2 (Test-Team)
        detail_url = reverse("installation-detail", kwargs={"pk": installation_id})
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "id": installation_id,
                "attributes": {"from_timestamp_s": 1601510000, "is_public": True},
            }
        }
        response = self.client.patch(detail_url, data=request_data)
        # Expect a HTTP 404 error code, because the object to be patched should not be
        # accessible to the authenticated user.
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_patch_no_owner(self):
        """PATCH /installations/ of an organization where the user ist not an OWNER."""
        # Need a different user for this test case.
        # User horstHilfsarbeiter is ASSISTANT in Versuchsverbung (pk=2).
        self.authenticate(username="horstHilfsarbeiter", password="horst")
        request_data = {
            "data": {
                "type": format_resource_type("Installation"),
                "id": 2,
                "attributes": {"from_timestamp_s": 1601510000, "is_public": False},
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        # Expect a HTTP 403 error code, because the user has access to the Node but is
        # not sufficiently privileged to alter it.
        self.assertEqual(response.status_code, 403)

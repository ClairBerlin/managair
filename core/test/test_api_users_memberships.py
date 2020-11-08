from unittest import skip

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type


class UsersTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Members of Versuchsverbund are the users with
        # pk 4: Horst Hilfsarbeiter
        # pk 6: Ingo Inspekteur
        # pk 7: Priska Prüferin
        self.client.login(username="veraVersuch", password="versuch")
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("user-detail", kwargs={"pk": 3})
        self.collection_url = reverse("user-list")

    def tearDown(self):
        self.client.logout()

    def test_get_users(self):
        """GET /users/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 7)

    # TODO: GET a specific room via query-parameter.

    def test_get_user(self):
        """GET /users/<user_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "veraVersuch")
        self.assertEqual(response.data["email"], "vera@versuch.de")

    @skip(
        "Test fails because of upstream bug: https://github.com/django-json-api/django-rest-framework-json-api/issues/859"
    )
    def test_get_user_organizations(self):
        """GET /users/<user_id>/organizations/"""
        url = reverse(
            "user-related", kwargs={"pk": 3, "related_field": "organizations"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class MembershipsTestCase(APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # priskaPrueferin is OWNER of Versuchsverbund, Membership pk=15;
        # and ASSISTANT in Test-Team, Membership pk=16.
        self.client.login(username="priskaPrueferin", password="priska")
        self.mid = 15
        self.detail_url = reverse("membership-detail", kwargs={"pk": self.mid})
        self.collection_url = reverse("membership-list")

    def tearDown(self):
        self.client.logout()

    def test_get_memberships(self):
        """GET /memberships/"""
        response = self.client.get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 8)

    # TODO: GET memberships for a specific organization or user via query-parameters.

    def test_get_membership(self):
        """GET /memberships/<membership_id>/"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "O")

    def test_patch_membership(self):
        """PATCH /membership/<membership_id>/"""
        request_data = {
            "data": {
                "type": format_resource_type("Membership"),
                "id": self.mid,
                "attributes": {"role": "I"},  # Downgrade to INSPECTOR role.
            }
        }
        response = self.client.patch(self.detail_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "I")

    def test_create_get_delete_membership(self):
        request_data = {
            "data": {
                "type": format_resource_type("Membership"),
                "attributes": {
                    "role": "A",
                },
                "relationships": {
                    # Make annaAngestellte (pk=5) a Versuchsverbund (pk=2) ASSISTANT.
                    "user": {"data": {"type": format_resource_type("User"), "id": "5"}},
                    "organization": {
                        "data": {
                            "type": format_resource_type("Organization"),
                            "id": "2",
                        }
                    },
                },
            }
        }
        # POST /memberships/
        response1 = self.client.post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["role"], "A")
        self.assertEqual(response1.data["user"]["id"], "5")
        self.assertEqual(response1.data["organization"]["id"], "2")
        # Fetch the membership resource just created.
        response_url = response1.data["url"]
        # GET /memberships/<membership_id/>
        response2 = self.client.get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["role"], "A")
        self.assertEqual(response2.data["user"]["id"], "5")
        self.assertEqual(response2.data["organization"]["id"], "2")
        # Delete the membership.
        # DELETE /memberships/<membership_id>/
        response3 = self.client.delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /memberships/<membership_id>/
        response4 = self.client.get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_membership_user(self):
        """GET /memberships/<membership_id>/user/"""
        url = reverse("membership-related", kwargs={"pk": 15, "related_field": "user"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "priskaPrueferin")

    def test_get_membership_organization(self):
        """GET /memberships/<membership_id>/organization/"""
        url = reverse(
            "membership-related", kwargs={"pk": 15, "related_field": "organization"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsverbund")

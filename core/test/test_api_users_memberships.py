from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_json_api.utils import format_resource_type
from .utils import TokenAuthMixin


class UsersTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # veraVersuch is owner of the organization Versuchsverbund with pk=2.
        # Members of Versuchsverbund are the users with
        # pk 4: Horst Hilfsarbeiter
        # pk 6: Ingo Inspekteur
        # pk 7: Priska Prüferin
        self.auth_response, self.auth_token = self.authenticate(
            username="veraVersuch", password="versuch"
        )
        self.assertIsNotNone(self.auth_token)
        # Versuchsverbund owns
        # Clairchen Schwarz (id=3b95a1b2-74e7-9e98-52c4-4acae441f0ae) and
        # ERS Test-Node (id=9d02faee-4260-1377-22ec-936428b572ee).
        self.detail_url = reverse("user-detail", kwargs={"pk": 3})
        self.collection_url = reverse("user-list")

    def tearDown(self):
        self.logout()

    def test_get_users(self):
        """GET /users/"""
        response = self.auth_get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 7)

    def test_get_users_search(self):
        """GET /users/?filter[search]=<search-text>"""
        response = self.auth_get(self.collection_url, {"filter[search]": "tom"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "tomTester")

    def test_get_users_in_organization(self):
        """GET /users/?filter[organization]=<organization_id>"""
        response = self.auth_get(self.collection_url, {"filter[organization]": "2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 4)

    def test_get_user(self):
        """GET /users/<user_id>/"""
        response = self.auth_get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "veraVersuch")
        self.assertEqual(response.data["email"], "vera@versuch.de")

    def test_get_user_organizations(self):
        """GET /users/<user_id>/organizations/"""
        url = reverse(
            "user-related", kwargs={"pk": 3, "related_field": "organizations"}
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Versuchsverbund")


class MembershipsTestCase(TokenAuthMixin, APITestCase):
    fixtures = ["user-fixtures.json", "inventory-fixtures.json"]

    def setUp(self):
        # priskaPrueferin (pk=7) is OWNER of Versuchsverbund, Membership pk=15;
        # and ASSISTANT in Test-Team, Membership pk=16.
        self.auth_response, self.auth_token = self.authenticate(
            username="priskaPrueferin", password="priska"
        )
        self.assertIsNotNone(self.auth_token)
        self.user_id = 7
        self.mid = 15
        self.detail_url = reverse("membership-detail", kwargs={"pk": self.mid})
        self.collection_url = reverse("membership-list")

    def tearDown(self):
        self.logout()

    def test_get_memberships(self):
        """GET /memberships/"""
        response = self.auth_get(self.collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 8)

    def test_get_membership_in_organization(self):
        """GET /memberships/?filter[organization]=<organization_id>"""
        response = self.auth_get(self.collection_url, {"filter[organization]": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 4)

    def test_get_membership_per_username(self):
        """GET /memberships/?filter[username]=<username>"""
        response = self.auth_get(
            self.collection_url, {"filter[username]": "ingoInspekteur"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_membership_per_user(self):
        """GET /memberships/?filter[user]=<user_id>"""
        response = self.auth_get(self.collection_url, {"filter[user]": 6})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_membership(self):
        """GET /memberships/<membership_id>/"""
        response = self.auth_get(self.detail_url)
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
        response = self.auth_patch(self.detail_url, data=request_data)
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
        response1 = self.auth_post(self.collection_url, data=request_data)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.data["role"], "A")
        self.assertEqual(response1.data["user"]["id"], "5")
        self.assertEqual(response1.data["organization"]["id"], "2")
        # Fetch the membership resource just created.
        response_url = response1.data["url"]
        # GET /memberships/<membership_id/>
        response2 = self.auth_get(response_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["role"], "A")
        self.assertEqual(response2.data["user"]["id"], "5")
        self.assertEqual(response2.data["organization"]["id"], "2")
        # Delete the membership.
        # DELETE /memberships/<membership_id>/
        response3 = self.auth_delete(response_url)
        self.assertEqual(response3.status_code, 204)
        # Make sure it is gone.
        # GET /memberships/<membership_id>/
        response4 = self.auth_get(response_url)
        self.assertEqual(response4.status_code, 404)

    def test_get_membership_user(self):
        """GET /memberships/<membership_id>/user/"""
        url = reverse("membership-related", kwargs={"pk": 15, "related_field": "user"})
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "priskaPrueferin")

    def test_get_membership_organization(self):
        """GET /memberships/<membership_id>/organization/"""
        url = reverse(
            "membership-related", kwargs={"pk": 15, "related_field": "organization"}
        )
        response = self.auth_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Versuchsverbund")

    def test_unauthorized_create_membership_no_member(self):
        """POST /memberships/ where the user is not a member of the organization."""
        # User tomTester (pk=2) is OWNER of Test-Team (pk=1).
        self.authenticate(username="tomTester", password="test")
        request_data = {
            "data": {
                "type": format_resource_type("Membership"),
                "attributes": {
                    "role": "A",
                },
                "relationships": {
                    # Make annaAngestellte (pk=5) a Versuchsverbund (pk=2) ASSISTANT.
                    "user": {"data": {"type": format_resource_type("User"), "id": 5}},
                    "organization": {
                        "data": {
                            "type": format_resource_type("Organization"),
                            "id": 2,
                        }
                    },
                },
            }
        }
        response = self.auth_post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_add_membership_no_member(self):
        """POST /memberships/ for a user that is not a member of the organization."""
        # Need a different user for this test case.
        # User tomTester (pk=2) is OWNER of Test-Team (pk=1).
        user_id = 2
        self.authenticate(username="tomTester", password="test")
        request_data = {
            "data": {
                "type": format_resource_type("Membership"),
                "attributes": {
                    "role": "A",
                },
                "relationships": {
                    # Make tomTester a Versuchsverbund (pk=2) ASSISTANT.
                    "user": {
                        "data": {"type": format_resource_type("User"), "id": user_id}
                    },
                    "organization": {
                        "data": {
                            "type": format_resource_type("Organization"),
                            "id": 2,
                        }
                    },
                },
            }
        }
        response = self.auth_post(self.collection_url, data=request_data)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_leave_organization(self):
        """DELETE /membership/ for a member that is not the OWNER of the organizatin."""
        # priskaPrüferin is ASSISTANT in Test-Team (membership pk=16).
        request_url = reverse("membership-detail", kwargs={"pk": 16})
        response = self.auth_delete(request_url)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_role_change_no_owner(self):
        """PATCH /membership/ for a member that is not OWNER of the organization."""
        # priskaPrüferin is ASSISTANT in Test-Team (membership pk=16).
        membership_id = 16
        request_url = reverse("membership-detail", kwargs={"pk": membership_id})
        request_data = {
            "data": {
                "type": format_resource_type("Membership"),
                "id": membership_id,
                "attributes": {"role": "O"},  # Attempt to self-upgrade.
            }
        }
        response = self.auth_patch(request_url, data=request_data)
        self.assertEqual(response.status_code, 403)

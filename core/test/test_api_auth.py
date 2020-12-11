from django.urls import reverse
from rest_framework.test import APITestCase


class AuthenticationTestCase(APITestCase):
    fixtures = ["user-fixtures.json"]
    login_url = reverse("rest_login")
    logout_url = reverse("rest_logout")
    email_login_request = {
        "data": {
            "type": "LoginView",
            "attributes": {"email": "anna@angestellte.de", "password": "anna"},
        }
    }

    def test_login_username(self):
        """POST /auth/login/"""
        request_data = {
            "data": {
                "type": "LoginView",
                "attributes": {"username": "annaAngestellte", "password": "anna"},
            }
        }
        response = self.client.post(self.login_url, data=request_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("key" in response.data)

    def test_login_email(self):
        """POST /auth/login/"""
        response = self.client.post(self.login_url, data=self.email_login_request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("key" in response.data)

    def test_authenticated_request(self):
        protocol_url = reverse("node-list")
        # Test unauthenticated request first.
        response1 = self.client.get(protocol_url)
        self.assertEqual(response1.status_code, 401)
        # Authenticate
        response2 = self.client.post(self.login_url, data=self.email_login_request)
        token = response2.data["key"]
        # Set AUTH header and make a simple request that requires authentication.
        response3 = self.client.get(protocol_url, HTTP_AUTHORIZATION=("Token " + token))
        self.assertEqual(response3.status_code, 200)

    def test_logout(self):
        protocol_url = reverse("node-list")
        # Authenticate
        response1 = self.client.post(self.login_url, data=self.email_login_request)
        token = response1.data["key"]
        # Set AUTH header and make a simple request that requires authentication.
        response2 = self.client.get(protocol_url, HTTP_AUTHORIZATION=("Token " + token))
        self.assertEqual(response2.status_code, 200)
        # Log Out
        response3 = self.client.post(
            self.logout_url, HTTP_AUTHORIZATION=("Token " + token)
        )
        self.assertEqual(response3.status_code, 200)
        # Attempt another request.
        response4 = self.client.get(protocol_url, HTTP_AUTHORIZATION=("Token " + token))
        self.assertEqual(response4.status_code, 401)


# class RegistrationTestCase(APITestCase):
#     fixtures = ["user-fixtures.json"]

#     registration_url = reverse("rest_register")
#     verification_url = reverse("rest_verify_email")
#     registration_request = {
#         "data": {
#             "type": "RegisterView",
#             "attributes": {
#                 "username": "maxMustermann",
#                 "email": "max@mustermann.de",
#                 "password1": "mustermann",
#                 "password2": "mustermann",
#             },
#         }
#     }
#     verify_token_pattern = re.compile(
#         r"api/v1/auth/registration/account-confirm-email/(.*)/\n"
#     )
#     login_url = reverse("rest_login")
#     pwd_reset_url = reverse("rest_password_reset")
#     pwd_confirm_url = reverse("rest_password_reset_confirm")
#     confirm_token_pattern = re.compile(
#         r"api/v1/auth/password-reset/confirm/(.*)/(.*)/\n"
#     )

#     def test_registration(self):
#         response = self.client.post(
#             self.registration_url, data=self.registration_request
#         )
#         self.assertEqual(response.status_code, 201)

#     def test_registration_email(self):
#         response = self.client.post(
#             self.registration_url, data=self.registration_request
#         )
#         self.assertEqual(response.data["detail"], "Verification e-mail sent.")
#         # Test that one message has been sent.
#         self.assertEqual(len(mail.outbox), 1)
#         verification_email = mail.outbox[0]
#         self.assertEqual(
#             verification_email.subject,
#             "[Clair Plattform] Please Confirm Your E-mail Address",
#         )

#     def test_email_confirmation(self):
#         # Register a user.
#         self.client.post(self.registration_url, data=self.registration_request)
#         # Retrieve the email verification code.
#         email_body = mail.outbox[0].body
#         match = self.verify_token_pattern.search(email_body)
#         # POST the verification code
#         self.assertIsNotNone(match)
#         verification_token = match.group(1)
#         verification_request = {
#             "data": {
#                 "type": "VerifyEmailView",
#                 "attributes": {"key": verification_token},
#             }
#         }
#         response = self.client.post(self.verification_url, data=verification_request)
#         self.assertEqual(response.status_code, 200)
#         # Try to authenticate.
#         auth_request = {
#             "data": {
#                 "type": "LoginView",
#                 "attributes": {"email": "max@mustermann.de", "password": "mustermann"},
#             }
#         }
#         response = self.client.post(self.login_url, data=auth_request)
#         self.assertEqual(response.status_code, 200)

#     def test_reset_password(self):
#         # User annaAngesteller has lost her password. She is not authenticated.
#         reset_request = {
#             "data": {
#                 "type": "PasswordResetView",
#                 "attributes": {"email": "anna@angestellte.de"},
#             }
#         }
#         response1 = self.client.post(self.pwd_reset_url, data=reset_request)
#         self.assertEqual(response1.status_code, 200)
#         self.assertEqual(len(mail.outbox), 1)
#         email_body = mail.outbox[0].body
#         match = self.confirm_token_pattern.search(email_body)
#         # POST the confirmation code.
#         self.assertIsNotNone(match)
#         confirmation_uid = match.group(1)
#         confirmation_token = match.group(2)
#         new_pwd = "angestellte"
#         confirmation_request = {
#             "data": {
#                 "type": "PasswordResetConfirmView",
#                 "attributes": {
#                     "uid": confirmation_uid,
#                     "token": confirmation_token,
#                     "new_password1": new_pwd,
#                     "new_password2": new_pwd,
#                 },
#             }
#         }
#         response2 = self.client.post(self.pwd_confirm_url, data=confirmation_request)
#         self.assertEqual(response2.status_code, 200)
#         # Attempt to authenticate with new password.
#         auth_request = {
#             "data": {
#                 "type": "LoginView",
#                 "attributes": {"email": "anna@angestellte.de", "password": new_pwd},
#             }
#         }
#         response3 = self.client.post(self.login_url, data=auth_request)
#         self.assertEqual(response3.status_code, 200)

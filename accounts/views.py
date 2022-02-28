from django.contrib.auth.password_validation import password_validators_help_text_html
from allauth.account.views import SignupView
from allauth.account.forms import SignupForm, PasswordField
from allauth.account import app_settings
from allauth.utils import set_form_field_order
from django.utils.translation import gettext_lazy as _


class CustomForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(CustomForm, self).__init__(*args, **kwargs)
        self.fields["password1"] = PasswordField(
            label=_("Password"),
            autocomplete="new-password",
            help_text=password_validators_help_text_html(),
        )
        if app_settings.SIGNUP_PASSWORD_ENTER_TWICE:
            self.fields["password2"] = PasswordField(label=_("Password (again)"))

        if hasattr(self, "field_order"):
            set_form_field_order(self, self.field_order)


class AccountSignupView(SignupView):
    form_class = CustomForm


account_signup_view = AccountSignupView.as_view()

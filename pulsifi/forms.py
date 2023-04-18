"""
    Forms in pulsifi app.
"""

import logging

from allauth.account.forms import LoginForm as Base_LoginForm, SignupForm as Base_SignupForm
from django import forms
from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.utils import timezone
from pulsifi.models import Pulse, Reply, User

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


class BaseFormConfig(forms.Form):
    """
        Config class to provide the base attributes for how to configure a
        form.
    """

    template_name = "pulsifi/base_form_snippet.html"
    """
        Link to a HTML snippet, which describes how the form should be rendered
        (see https://docs.djangoproject.com/en/4.1/topics/forms/#reusable-form-templates).
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        visible_field: forms.BoundField
        for visible_field in self.visible_fields():
            if visible_field.widget_type not in ("checkbox", "radio"):
                visible_field.field.widget.attrs["class"] = "form-control"

        self.label_suffix = ""


class Login_Form(BaseFormConfig, Base_LoginForm):
    """ Form to customise the HTML & CSS generated for the login form. """

    prefix = "login"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["login"].label = "Username / Email Address"
        self.fields["login"].widget.attrs["placeholder"] = "Enter your Username / Email Address"

        self.fields["password"].widget.attrs["placeholder"] = "Enter your Password"


class Signup_Form(BaseFormConfig, Base_SignupForm):
    """ Form to customise the HTML & CSS generated for the signup form. """

    prefix = "signup"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["email"].label = "Email Address"
        self.fields["email"].widget.attrs["placeholder"] = "Enter your Email Address"
        # noinspection PyProtectedMember
        email_required_error_message: str = get_user_model()._meta.get_field("email").error_messages["blank"]
        self.fields["email"].error_messages["required"] = email_required_error_message
        self.fields["email"].default_error_messages["required"] = "This is a required field."

        self.fields["username"].widget.attrs["placeholder"] = "Choose a Username"
        # noinspection PyProtectedMember
        self.fields["username"].error_messages["required"] = get_user_model()._meta.get_field("username").error_messages["blank"]

        self.fields["password1"].widget.attrs["placeholder"] = "Choose a Password"
        # noinspection PyProtectedMember
        self.fields["password1"].error_messages["required"] = get_user_model()._meta.get_field("password").error_messages["blank"]

        self.fields["password2"].label = "Confirm Password"
        self.fields["password2"].widget.attrs["placeholder"] = "Re-enter your Password, to check that you can spell"
        # noinspection PyProtectedMember
        self.fields["password2"].error_messages["required"] = get_user_model()._meta.get_field("password").error_messages["blank"]

    def clean(self) -> dict[str]:
        """
            Validate inserted form data using temporary in-memory
            :model:`pulsifi.user` object.
        """

        super().clean()

        non_empty_fields: set[str] = set()
        field_name: str
        for field_name in self.fields:
            if field_name != "password2" and self.cleaned_data.get(field_name):
                non_empty_fields.add(field_name)

        try:
            get_user_model()(
                username=self.cleaned_data.get("username"),
                password=self.cleaned_data.get("password1"),
                email=self.cleaned_data.get("email")
            ).full_clean()
        except ValidationError as e:
            self.add_errors_from_validation_error_exception(e, non_empty_fields)

        if self.errors.get("password1") and any("common" in error for error in self.errors["password1"]) and any("short" in error for error in self.errors["password1"]):
            self._errors["password1"] = [error for error in self._errors["password1"] if "common" not in error]

        return self.cleaned_data

    def add_errors_from_validation_error_exception(self, exception: ValidationError, non_empty_fields: set[str] = None, model_field_name: str = None) -> None:
        """
            Adds the error message(s) from any caught ValidationError
            exceptions to the forms errors dictionary/list.
        """

        if non_empty_fields is None:
            non_empty_fields = set()
        else:
            if "password1" in non_empty_fields:
                non_empty_fields.remove("password1")
                non_empty_fields.add("password")
            non_empty_fields.discard("password2")

        if not hasattr(exception, "error_dict") and hasattr(exception, "error_list") and model_field_name:
            error: ValidationError
            for error in exception.error_list:
                if model_field_name in non_empty_fields or ("null" not in error.message and "required field" not in error.message):
                    self.add_error(model_field_name, error)

        elif hasattr(exception, "error_dict"):
            field_name: str
            errors: list[ValidationError]
            for field_name, errors in exception.error_dict.items():
                if field_name == "__all__":
                    self.add_error(None, errors)

                elif field_name == "password":
                    if "password" in non_empty_fields:
                        self.add_error("password1", errors)

                    else:
                        self.add_error("password1", [error for error in errors if self.fields["password1"].error_messages["required"] not in error.message])

                else:
                    if field_name in non_empty_fields:
                        self.add_error(field_name, errors)

                    else:
                        self.add_error(field_name, [error for error in errors if self.fields[field_name].error_messages["required"] not in error.message])

        else:
            logging.error(f"Validation error {repr(exception)} raised without a field name supplied.")


class Pulse_Form(BaseFormConfig, forms.ModelForm):
    """ Form for creating a new Pulse """

    prefix = "create_pulse"

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        model = Pulse
        fields = ("message",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["message"].label = "What are you thinking...?"
        self.fields["message"].widget.attrs["placeholder"] = "What are you thinking...?"


class Reply_Form(BaseFormConfig, forms.ModelForm):
    """ Form for creating a new reply. """

    prefix = "create_reply"

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        model = Reply
        fields = ("message", "_content_type", "_object_id")
        widgets = {
            "_content_type": forms.HiddenInput,
            "_object_id": forms.HiddenInput
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.creator: User | None = None

        self.fields["message"].label = "Reply message..."
        self.fields["message"].widget.attrs["placeholder"] = "Reply message..."

    def clean(self) -> dict[str]:
        """
            Validate inserted form data using temporary in-memory
            :model:`pulsifi.reply` object.
        """

        creation_time: timezone.datetime = timezone.now()

        super().clean()

        if not self.creator:
            raise ValueError("\"creator\" property must be set on this form instance in order to clean this form.")

        if (creation_time - Reply(creator=self.creator, _object_id=self.cleaned_data["_object_id"], _content_type=self.cleaned_data["_content_type"]).get_latest_reply_of_same_original_pulse().date_time_created) < settings.MIN_TIME_BETWEEN_REPLIES_ON_SAME_POST:
            raise ValidationError("Cannot create Reply so soon after already creating a Reply under this original Pulse.", code="too_recent")

        return self.cleaned_data


class Bio_Form(BaseFormConfig, forms.ModelForm):
    """ Form for updating a user's bio. """

    prefix = "update_bio"

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        model = get_user_model()
        fields = ("bio",)

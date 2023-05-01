"""
    Views in pulsifi app.
"""

import logging
from typing import Callable

from allauth.account.views import LoginView as Base_LoginView, SignupView as Base_SignupView
from django import shortcuts as django_shortcuts, urls as django_urls
from django.apps import apps
from django.conf import settings
from django.contrib import auth
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, RedirectView
from django.views.generic.base import TemplateView
from el_pagination.views import AjaxListView

from pulsifi.forms import Bio_Form, Login_Form, Signup_Form
from pulsifi.models import Pulse, Reply, User
from . import post_request_checkers
from .mixins import CanLoginMixin, PostRequestCheckerMixin, PulseListMixin, RedirectAuthenticatedUserMixin
from .post_request_checkers import Template_View_Mixin_Protocol

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


class Home_View(RedirectAuthenticatedUserMixin, TemplateView):  # TODO: toast for account deletion, ask to log in when redirecting here (show modal)
    template_name = "pulsifi/home.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs) -> dict[str, ...]:
        context = super().get_context_data(**kwargs)

        if "login_form" not in kwargs and "login_form" not in self.request.session:
            context["login_form"] = Login_Form(prefix="login")

        elif "login_form" in kwargs:
            context["login_form"] = kwargs["login_form"]

        elif "login_form" in self.request.session:
            login_form = Login_Form(
                data=self.request.session["login_form"]["data"],
                request=self.request,
                prefix="login"
            )
            login_form.is_valid()

            context["login_form"] = login_form

            del self.request.session["login_form"]

        if "signup_form" not in kwargs and "signup_form" not in self.request.session:
            context["signup_form"] = Signup_Form(prefix="signup")

        elif "signup_form" in kwargs:
            context["signup_form"] = kwargs["signup_form"]

        elif "signup_form" in self.request.session:
            signup_form = Signup_Form(
                data=self.request.session["signup_form"]["data"],
                prefix="signup"
            )
            signup_form.is_valid()

            context["signup_form"] = signup_form

            del self.request.session["signup_form"]

        # noinspection PyArgumentList
        if self.request.GET.get(key="action") in ("login", "signup"):
            try:
                context["redirect_field_value"] = self.request.GET[self.redirect_field_name]
            except KeyError:
                logging.error(
                    f"redirect_field_value could not be added to template context because the value was not found in the GET parameter with key: \"{self.redirect_field_name}\""
                )

        context["redirect_field_name"] = self.redirect_field_name

        return context


class Feed_View(PulseListMixin, CanLoginMixin, AjaxListView):  # TODO: only show pulses/replies if within time & visible & creator is active+visible & not in any non-rejected reports, toast for successful redirect after login
    template_name = "pulsifi/feed.html"

    def get_queryset(self) -> set[Pulse]:
        user: User = self.request.user

        if self.request.method == "GET" and "highlight" in self.request.GET:
            model_name: str
            object_id: str
            # noinspection PyUnresolvedReferences
            model_name, _, object_id = self.request.GET["highlight"].partition("_")
            if model_name == "pulse" and object_id.isdecimal():
                return user.get_feed_pulses(exclude={object_id})

        return user.get_feed_pulses()

    def get_context_data(self, **kwargs) -> dict[str, ...]:
        context = super().get_context_data(**kwargs)

        if self.request.method == "GET" and "highlight" in self.request.GET:
            model_name: str
            object_id: str
            # noinspection PyUnresolvedReferences
            model_name, _, object_id = self.request.GET["highlight"].partition("_")
            if model_name in {"pulse", "reply"} and object_id.isdecimal():
                try:
                    highlight: Pulse | Reply = apps.get_model(app_label="pulsifi", model_name=model_name).objects.get(id=object_id, is_visible=True)

                    if highlight.hidden_by_reports:
                        context["highlight"] = highlight
                    else:
                        context["failed_highlight"] = "The requested content could not be highlighted because too many completed reports have been made about the content's creator"

                except (Pulse.DoesNotExist, Reply.DoesNotExist):
                    context["failed_highlight"] = "The requested content could not be highlighted"

            else:
                context["failed_highlight"] = "The requested content could not be highlighted"

        return context


class Self_Account_View(CanLoginMixin, RedirectView):  # TODO: Show toast for users that have just signed up or just edited their bio/avatar
    query_string = True

    def get_redirect_url(self, *args, **kwargs) -> str:
        return django_urls.reverse(
            "pulsifi:specific_account",
            kwargs={"username": self.request.user.username}
        )


class Specific_Account_View(PulseListMixin, CanLoginMixin, AjaxListView):  # TODO: only show pulses/replies if within time & visible, change profile parts (if self profile), delete account with modal toast for account creation
    template_name = "pulsifi/account.html"

    def get_context_data(self, **kwargs) -> dict[str, ...]:
        context = super().get_context_data(**kwargs)

        if self.kwargs.get("username") == self.request.user.username and "update_bio_form" not in context:
            user: User = self.request.user
            context["update_bio_form"] = Bio_Form(
                prefix="update_bio",
                initial={"bio": user.bio}
            )

        context["specific_account"] = django_shortcuts.get_object_or_404(
            get_user_model(),
            is_active=True,
            username=self.kwargs.get("username")
        )

        context["hidden"] = False

        if context["specific_account"].hidden_by_reports:
            context["hidden"] = "Too many completed reports made about this user"

        return context

    def get_queryset(self) -> set[Pulse]:
        return {pulse for pulse in django_shortcuts.get_object_or_404(
            get_user_model(),
            is_active=True,
            username=self.kwargs.get("username")
        ).created_pulse_set.filter(is_visible=True) if not pulse.hidden_by_reports}

    @classmethod
    def get_post_request_checker_functions(cls) -> set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]]:
        return super().get_post_request_checker_functions() | {
            post_request_checkers.check_follow_or_unfollow_in_post_request,
            post_request_checkers.check_update_bio_in_post_request
        }


class Related_Users_View(CanLoginMixin, ListView, PostRequestCheckerMixin):
    template_name = "pulsifi/related_users.html"
    context_object_name = "related_user_list"

    @classmethod
    def get_post_request_checker_functions(cls) -> set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]]:
        return super().get_post_request_checker_functions() | {
            post_request_checkers.check_follow_or_unfollow_in_post_request
        }


class Following_View(Related_Users_View):
    extra_context = {"follow_form": True}

    def get_queryset(self) -> models.QuerySet[User]:
        return get_user_model().objects.annotate(models.Count("followers")).filter(
            followers=self.request.user
        ).order_by("-followers__count")


class Followers_View(Related_Users_View):
    def get_queryset(self) -> models.QuerySet[User]:
        return get_user_model().objects.annotate(models.Count("followers")).filter(
            following=self.request.user
        ).order_by("-followers__count")


# TODO: profile search view, leaderboard view


class Signup_POST_View(Base_SignupView):
    http_method_names = ["post"]
    redirect_authenticated_user = True
    prefix = "signup"

    def form_invalid(self, form) -> HttpResponseRedirect:  # TODO: check if errors show
        if "signup_form" in self.request.session:
            del self.request.session["signup_form"]

        self.request.session["signup_form"] = {
            "data": form.data,
            "errors": form.errors
        }

        return django_shortcuts.redirect(settings.SIGNUP_URL)


class Login_POST_View(Base_LoginView):
    http_method_names = ["post"]
    redirect_authenticated_user = True
    prefix = "login"

    def form_invalid(self, form) -> HttpResponseRedirect:
        if "login_form" in self.request.session:
            del self.request.session["login_form"]

        self.request.session["login_form"] = {
            "data": form.data,
            "errors": form.errors
        }

        return django_shortcuts.redirect(settings.LOGIN_URL)

# TODO: password change view, confirm email view, manage emails view, password set after not having one because of social login view, forgotten password reset view, forgotten password reset success view, logout confirmation popup (toast)

# TODO: 2fa stuff!

# TODO: 404 error page, 403 forbidden page when reports cannot be created, other nicer error pages (look up all possible http errors)

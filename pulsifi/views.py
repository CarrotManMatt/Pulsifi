"""
    Views in pulsifi app.
"""
from typing import Callable, Iterable, Protocol, Type

from allauth.account.views import LoginView as Base_LoginView, SignupView as Base_SignupView
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import RedirectURLMixin
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse
from django.views.generic import CreateView, ListView, RedirectView
from django.views.generic.base import ContextMixin, TemplateView
from django.views.generic.list import MultipleObjectMixin
from el_pagination.views import AjaxListView

from .exceptions import GETParameterError, RedirectionLoopError
from .forms import Login_Form, Signup_Form
from .models import Pulse, Reply, User


class _GenericViewMixin(Protocol):
    request: HttpRequest


def _check_follow_or_unfollow_in_POST_request(self: _GenericViewMixin) -> bool | HttpResponse:
    try:
        action: str = self.request.POST["action"].lower()
    except KeyError:
        return False
    else:
        if action != "follow" and action != "unfollow":
            return False

        if action == "follow":
            try:
                follow_user: User = get_user_model().objects.get(id=self.request.POST["follow_user_id"])
            except (KeyError, get_user_model().DoesNotExist):
                return HttpResponseBadRequest()
            else:
                if self.request.user not in follow_user.followers.all():
                    follow_user.followers.add(self.request.user)
                    return redirect(self.request.path_info)
                else:
                    return HttpResponseBadRequest()
        elif action == "unfollow":
            try:
                unfollow_user: User = get_user_model().objects.get(id=self.request.POST["unfollow_user_id"])
            except (KeyError, get_user_model().DoesNotExist):
                return HttpResponseBadRequest()
            else:
                if self.request.user in unfollow_user.followers.all():
                    unfollow_user.followers.remove(self.request.user)
                    return redirect(self.request.path_info)
                else:
                    return HttpResponseBadRequest()


def _check_like_or_dislike_in_POST_request(self: _GenericViewMixin) -> bool | HttpResponse:
    try:
        action: str = self.request.POST["action"].lower()
    except KeyError:
        return False
    else:
        if action != "like" and action != "dislike":
            return False

        try:
            model: Type[Pulse | Reply] = apps.get_model(app_label="pulsifi", model_name=self.request.POST["actionable_model_name"])
        except KeyError:
            return HttpResponseBadRequest()
        else:
            if action == "like":
                try:
                    actionable_object: Pulse | Reply = model.objects.get(id=self.request.POST["likeable_object_id"])
                except (KeyError, model.DoesNotExist):
                    return HttpResponseBadRequest()
                else:
                    actionable_object.liked_by.add(self.request.user)
                    return redirect(self.request.path_info)
            elif action == "dislike":
                try:
                    actionable_object: Pulse | Reply = model.objects.get(id=self.request.POST["dislikeable_object_id"])
                except (KeyError, model.DoesNotExist):
                    return HttpResponseBadRequest()
                else:
                    actionable_object.disliked_by.add(self.request.user)
                    return redirect(self.request.path_info)


# def check_reply_in_post_request(self) -> bool | Reply | Reply_Form:
#     try:
#         action: str = self.request.POST["action"]
#     except KeyError:
#         return HttpResponseBadRequest()
#     else:
#         if action == "reply":
#             form = Reply_Form(self.request.POST)
#             if form.is_valid():
#                 reply: Reply = form.save()
#                 return redirect(reply)
#             else:
#                 return self.render_to_response(self.get_context_data(form=form))
#         else:
#             return HttpResponseBadRequest()


class POSTRequestCheckerMixin:
    POST_request_checker_functions: Iterable[Callable[[_GenericViewMixin], bool | HttpResponse]] = ()

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # noinspection PyUnresolvedReferences
        if hasattr(super(), "post") and callable(super().post):
            # noinspection PyUnresolvedReferences
            return super().post(request, *args, **kwargs)

        for POST_request_checker_function in self.POST_request_checker_functions:
            # noinspection PyTypeChecker
            if response := POST_request_checker_function(self):
                return response
        else:
            return HttpResponseBadRequest()


class PulseListMixin(POSTRequestCheckerMixin, MultipleObjectMixin, ContextMixin):
    POST_request_checker_functions = (_check_like_or_dislike_in_POST_request,)
    object_list: QuerySet[Pulse] = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.object_list = self.get_queryset()

        context.update(
            {
                "pulse_list": self.object_list,
                "pagination_snippet": "pulsifi/feed_pagination_snippet.html"
            }
        )
        return context


class FollowUserMixin(POSTRequestCheckerMixin):
    POST_request_checker_functions = (_check_follow_or_unfollow_in_POST_request,)


class RedirectAuthenticatedUserMixin(Base_RedirectAuthenticatedUserMixin):
    request: HttpRequest
    redirect_field_name = DEFAULT_REDIRECT_FIELD_NAME

    def get_success_url(self):
        return allauth_utils.get_next_redirect_url(self.request, self.redirect_field_name) or allauth_utils.get_login_redirect_url(self.request)


class Home_View(RedirectAuthenticatedUserMixin, TemplateView):  # TODO: toast for account deletion, show admin link for super-users, ask to log in when redirecting here (show modal), prevent users with >3 in progress reports or >0 completed reports from logging in (with reason page)
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
                pass

        context["redirect_field_name"] = self.redirect_field_name

        return context


class Feed_View(PulseListMixin, LoginRequiredMixin, AjaxListView):  # TODO: POST actions for pulses & replies, only show pulses/replies if within time & visible & creator is active+visible & not in any non-rejected reports, show replies, toast for successful redirect after login, highlight pulse/reply (from get parameters) at top of page or message if not visible
    template_name = "pulsifi/feed.html"

    def get(self, request, *args, **kwargs):
        try:
            return self.render_to_response(self.get_context_data())
        except GETParameterError:
            return HttpResponseBadRequest()

    def get_queryset(self):
        user: User = self.request.user
        queryset: QuerySet[Pulse] = user.get_feed_pulses()

        if self.request.method == "GET" and "highlight" in self.request.GET:
            highlight: str = self.request.GET["highlight"]

            try:
                return queryset.exclude(id=int(highlight))
            except ValueError as e:
                raise GETParameterError(get_parameters={"highlight": highlight}) from e

        return queryset


class Self_Account_View(LoginRequiredMixin, RedirectView):  # TODO: Show toast for users that have just signed up to edit their bio/avatar
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "pulsifi:specific_account",
            kwargs={"username": self.request.user.username}
        )


class Specific_Account_View(FollowUserMixin, PulseListMixin, LoginRequiredMixin, AjaxListView):  # TODO: POST actions for pulses & replies, only show pulses/replies if within time & visible & creator is active+visible & not in any non-rejected reports, change profile parts (if self profile), delete account with modal or view all finished pulses (if self profile), show replies, toast for account creation, prevent create new pulses/replies if >3 in progress or >1 completed reports on user or pulse/reply of user
    template_name = "pulsifi/account.html"
    POST_request_checker_functions = (_check_follow_or_unfollow_in_POST_request, _check_like_or_dislike_in_POST_request)
    object_list = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["specific_account"] = get_object_or_404(
            get_user_model(),
            is_active=True,
            username=self.kwargs.get("username")
        )

        return context

    def get_queryset(self):
        return get_object_or_404(
            get_user_model(),
            is_active=True,
            username=self.kwargs.get("username")
        ).created_pulse_set.all()


class Following_View(FollowUserMixin, LoginRequiredMixin, ListView):  # TODO: Inherit from combined following/followers view
    template_name = "pulsifi/related_users.html"
    context_object_name = "related_user_list"
    extra_context = {"follow_form": True}
    object_list = None  # HACK: set object_list to None to prevent not set error

    def get_queryset(self):
        return get_user_model().objects.annotate(Count("followers")).filter(followers=self.request.user).order_by("-followers__count")


class Followers_View(FollowUserMixin, LoginRequiredMixin, ListView):  # TODO: Inherit from combined following/followers view
    template_name = "pulsifi/related_users.html"
    context_object_name = "related_user_list"
    object_list = None  # HACK: set object_list to None to prevent not set error

    def get_queryset(self):
        return get_user_model().objects.annotate(Count("followers")).filter(following=self.request.user).order_by("-followers__count")


# TODO: profile search view, leaderboard view, report views


class Create_Pulse_View(LoginRequiredMixin, CreateView):
    pass


class Signup_POST_View(Base_SignupView):
    http_method_names = ["post"]
    redirect_authenticated_user = True
    prefix = "signup"

    def form_invalid(self, form):
        if "signup_form" in self.request.session:
            del self.request.session["signup_form"]

        self.request.session["signup_form"] = {
            "data": form.data,
            "errors": form.errors
        }

        return redirect(settings.SIGNUP_URL)


class Login_POST_View(Base_LoginView):
    http_method_names = ["post"]
    redirect_authenticated_user = True
    prefix = "login"

    def form_invalid(self, form):
        if "login_form" in self.request.session:
            del self.request.session["login_form"]

        self.request.session["login_form"] = {
            "data": form.data,
            "errors": form.errors
        }

        return redirect(settings.LOGIN_URL)

# TODO: password change view, confirm email view, manage emails view, password set after not having one because of social login view, forgotten password reset view, forgotten password reset success view, logout confirmation popup (toast)

# TODO: 2fa stuff!

# TODO: 404 error page, 403 forbidden page when reports cannot be created, other nicer error pages (look up all possible http errors)

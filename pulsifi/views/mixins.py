from typing import Callable

from allauth.account import utils as allauth_utils
from allauth.account.views import RedirectAuthenticatedUserMixin as Base_RedirectAuthenticatedUserMixin
from django.contrib.auth import REDIRECT_FIELD_NAME as DEFAULT_REDIRECT_FIELD_NAME
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.generic.base import ContextMixin
from el_pagination.views import MultipleObjectMixin

from pulsifi.forms import Pulse_Form, Reply_Form, Report_Form
from pulsifi.models import Pulse
from pulsifi.views import post_request_checkers
from pulsifi.views.post_request_checkers import Template_View_Mixin_Protocol


class PostRequestCheckerMixin(Template_View_Mixin_Protocol):
    post_request_checker_functions: set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]] = set()

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if callable(getattr(super(), "post", None)):
            # noinspection PyUnresolvedReferences
            return super().post(request, *args, **kwargs)

        else:
            post_request_checker_function: Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]
            for post_request_checker_function in self.get_post_request_checker_functions():
                if response := post_request_checker_function(self):
                    return response

            else:
                return HttpResponseBadRequest()

    @classmethod
    def get_post_request_checker_functions(cls) -> set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]]:
        return cls.post_request_checker_functions


class PulseListMixin(MultipleObjectMixin, ContextMixin, PostRequestCheckerMixin):
    object_list: models.QuerySet[Pulse]
    context_object_name: str = "pulse_list"

    def get_context_data(self, **kwargs) -> dict[str, ...]:
        self.object_list = self.get_queryset()

        context = {"view": self, "content_iterate_snippet": "pulsifi/content_iterate_snippet.html"} | kwargs

        context_object_name = self.get_context_object_name(self.object_list)
        if context_object_name is not None:
            context[context_object_name] = self.object_list

        if "create_pulse_form" not in context:
            context["create_pulse_form"] = Pulse_Form(prefix="create_pulse")
        if "create_reply_form" not in context:
            context["create_reply_form"] = Reply_Form(prefix="create_reply")
        if "create_report_form" not in context:
            context["create_report_form"] = Report_Form(prefix="create_report")

        return context

    @classmethod
    def get_post_request_checker_functions(cls) -> set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]]:
        return super().get_post_request_checker_functions() | {
            post_request_checkers.check_add_or_remove_like_or_dislike_in_post_request,
            post_request_checkers.check_create_pulse_or_reply_or_report_in_post_request
        }


class RedirectAuthenticatedUserMixin(Base_RedirectAuthenticatedUserMixin):
    request: HttpRequest
    redirect_field_name = DEFAULT_REDIRECT_FIELD_NAME

    def get_success_url(self):
        return allauth_utils.get_next_redirect_url(
            self.request,
            self.redirect_field_name
        ) or allauth_utils.get_login_redirect_url(
            self.request
        )

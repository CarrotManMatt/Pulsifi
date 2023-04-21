import logging
from typing import Callable

from allauth.account import utils as allauth_utils
from allauth.account.views import RedirectAuthenticatedUserMixin as Base_RedirectAuthenticatedUserMixin
from django.contrib.auth import REDIRECT_FIELD_NAME as DEFAULT_REDIRECT_FIELD_NAME
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.generic.base import ContextMixin
from el_pagination.views import MultipleObjectMixin
from pulsifi.forms import Reply_Form
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
                logging.debug(post_request_checker_function.__name__)
                if response := post_request_checker_function(self):
                    return response

            else:
                return HttpResponseBadRequest()

    @classmethod
    def get_post_request_checker_functions(cls) -> set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]]:
        return cls.post_request_checker_functions


class PulseListMixin(MultipleObjectMixin, ContextMixin, PostRequestCheckerMixin):
    object_list: models.QuerySet[Pulse]  # HACK: set object_list to None to prevent not set error

    def get_context_data(self, **kwargs) -> dict[str, ...]:
        context = super().get_context_data(**kwargs)

        self.object_list = self.get_queryset()
        context.update(
            {
                "pulse_list": self.object_list,
                "content_iterate_snippet": "pulsifi/content_iterate_snippet.html"
            }
        )

        if "reply_form" not in context:
            context["reply_form"] = Reply_Form(prefix="create_reply")

        return context

    @classmethod
    def get_post_request_checker_functions(cls) -> set[Callable[[Template_View_Mixin_Protocol], bool | HttpResponse]]:
        return super().get_post_request_checker_functions() | {
            post_request_checkers.check_add_or_remove_like_or_dislike_in_post_request,
            post_request_checkers.check_reply_in_post_request
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

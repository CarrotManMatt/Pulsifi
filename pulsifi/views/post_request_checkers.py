from typing import Protocol, Type

from django import shortcuts as django_shortcuts
from django.apps import apps
from django.contrib import auth
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse

from pulsifi.forms import Bio_Form, Pulse_Form, Reply_Form, Report_Form
from pulsifi.models import Pulse, Reply, User

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


class Template_View_Mixin_Protocol(Protocol):
    request: HttpRequest

    def render_to_response(self, context: dict[str, ...], **response_kwargs) -> TemplateResponse:
        ...

    def get_context_data(self, **kwargs) -> dict[str, ...]:
        ...


def check_follow_or_unfollow_in_post_request(view: Template_View_Mixin_Protocol) -> bool | HttpResponse:
    try:
        action: str = view.request.POST["action"].lower()
    except KeyError:
        return False

    else:
        if action != "follow" and action != "unfollow":
            return False

        if action == "follow":
            try:
                follow_user: User = get_user_model().objects.get(
                    id=view.request.POST["follow_user_id"]
                )

            except (KeyError, get_user_model().DoesNotExist):
                return HttpResponseBadRequest()

            else:
                if view.request.user not in follow_user.followers.all():
                    if follow_user == view.request.user:
                        return HttpResponseBadRequest("Cannot follow self")

                    # noinspection DjangoOrm
                    follow_user.followers.add(view.request.user)
                    return django_shortcuts.redirect(view.request.path_info)

                else:
                    return HttpResponseBadRequest()

        elif action == "unfollow":
            try:
                unfollow_user: User = get_user_model().objects.get(
                    id=view.request.POST["unfollow_user_id"]
                )

            except (KeyError, get_user_model().DoesNotExist):
                return HttpResponseBadRequest()

            else:
                if view.request.user in unfollow_user.followers.all():
                    unfollow_user.followers.remove(view.request.user)

                    return django_shortcuts.redirect(view.request.path_info)

                else:
                    return HttpResponseBadRequest()


def check_add_or_remove_like_or_dislike_in_post_request(view: Template_View_Mixin_Protocol) -> bool | HttpResponse:
    try:
        action: str = view.request.POST["action"].lower()
    except KeyError:
        return False

    else:
        if action not in {"like", "dislike", "remove_like", "remove_dislike"}:
            return False

        try:
            model: Type[Pulse | Reply] = apps.get_model(
                app_label="pulsifi",
                model_name=view.request.POST["actionable_model_name"]
            )

        except KeyError:
            return HttpResponseBadRequest()

        else:
            if action in {"like", "remove_like"}:
                try:
                    actionable_object: Pulse | Reply = model.objects.get(
                        id=view.request.POST["likeable_object_id"]
                    )

                except (KeyError, model.DoesNotExist):
                    return HttpResponseBadRequest()

                else:
                    if action == "like":
                        if actionable_object.creator == view.request.user:
                            return HttpResponseBadRequest("Cannot like own content")

                        actionable_object.liked_by.add(view.request.user)

                    elif action == "remove_like":
                        actionable_object.liked_by.remove(view.request.user)

                    return django_shortcuts.redirect(view.request.path_info)

            elif action in {"dislike", "remove_dislike"}:
                try:
                    actionable_object: Pulse | Reply = model.objects.get(
                        id=view.request.POST["dislikeable_object_id"]
                    )

                except (KeyError, model.DoesNotExist):
                    return HttpResponseBadRequest()

                else:
                    if action == "dislike":
                        if actionable_object.creator == view.request.user:
                            return HttpResponseBadRequest("Cannot dislike own content")

                        actionable_object.disliked_by.add(view.request.user)

                    elif action == "remove_dislike":
                        actionable_object.disliked_by.remove(view.request.user)

                    return django_shortcuts.redirect(view.request.path_info)


def check_create_pulse_or_reply_or_report_in_post_request(view: Template_View_Mixin_Protocol) -> bool | HttpResponse:
    try:
        action: str = view.request.POST["action"].lower()
    except KeyError:
        return False

    else:
        if action not in {"create_pulse", "create_reply", "create_report"}:
            return False

        if action == "create_pulse":
            pulse_form = Pulse_Form(view.request.POST, prefix="create_pulse")
            pulse_form.instance.creator = view.request.user
            if pulse_form.is_valid():
                return django_shortcuts.redirect(pulse_form.save())
            else:
                return view.render_to_response(
                    view.get_context_data(create_pulse_form=pulse_form)
                )

        elif action == "create_reply":
            reply_form = Reply_Form(view.request.POST, prefix="create_reply")
            reply_form.instance.creator = view.request.user
            if reply_form.is_valid():
                return django_shortcuts.redirect(reply_form.save())
            else:
                return view.render_to_response(
                    view.get_context_data(create_reply_form=reply_form)
                )

        elif action == "create_report":
            report_form = Report_Form(view.request.POST, prefix="create_report")
            report_form.instance.reporter = view.request.user
            if report_form.is_valid():
                report_form.save()
                return django_shortcuts.redirect("pulsifi:feed")
            else:
                return view.render_to_response(
                    view.get_context_data(create_report_form=report_form)
                )


def check_update_bio_in_post_request(view: Template_View_Mixin_Protocol) -> bool | HttpResponse:
    try:
        action: str = view.request.POST["action"].lower()
    except KeyError:
        return False

    else:
        if action != "update_bio":
            return False

        bio_form = Bio_Form(view.request.POST, prefix="update_bio")
        if bio_form.is_valid():
            user: User = view.request.user

            user.refresh_from_db()
            user.update(bio=bio_form.cleaned_data["bio"])

            return django_shortcuts.redirect(user)

        else:
            return view.render_to_response(
                view.get_context_data(update_bio_form=bio_form)
            )

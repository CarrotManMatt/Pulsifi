"""
    Extra Tags & Filters available for use in the templating engine within the
    pulsifi app.
"""

from re import Match as RegexMatch, sub as regex_sub

from django import template
from django.contrib import auth
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.options import Options as Model_Options
from django.template import defaultfilters, loader as template_utils
from django.utils import html as html_utils, safestring

from pulsifi.models import User

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage

register = template.Library()


# noinspection SpellCheckingInspection
@register.filter(needs_autoescape=True)
@defaultfilters.stringfilter
def format_mentions(value: str, autoescape=True) -> safestring.SafeString:
    """
        Formats the given string value, with any mentions of a user
        (E.g. @pulsifi) turned into the rendered HTML template of linking to
        that user (E.g. <a href="/user/@pulsifi">@pulsifi</a>)
    """

    if autoescape:
        esc_func = html_utils.conditional_escape
    else:
        # noinspection PyMissingOrEmptyDocstring
        def esc_func(x: str) -> str:
            return x

    def is_valid(possible_mention: RegexMatch) -> str:
        """
            Returns the HTML formatted mention if the regex match was a valid
            user, otherwise returns the original text.
        """

        possible_mention: str = possible_mention.group("mention")

        try:
            mentioned_user = get_user_model().objects.get(username=possible_mention)
        except get_user_model().DoesNotExist:
            return f"@{possible_mention}"

        return "".join([line.strip() for line in template_utils.render_to_string("pulsifi/mention_user_snippet.html", {"mentioned_user": mentioned_user}).splitlines()])

    return safestring.mark_safe(
        regex_sub(
            r"@(?P<mention>[\w.-]+)",
            is_valid,
            esc_func(value)
        )
    )


@register.simple_tag
def model_meta(obj: models.Model) -> bool | Model_Options:
    """
        Shortcut template tag to return the meta Model_Options container for the
        given model instance.
    """

    if not obj:
        return False

    # noinspection PyProtectedMember
    return obj._meta


@register.simple_tag
def model_content_type(obj: models.Model) -> bool | ContentType:
    """
        Shortcut template tag to return the corresponding ContentType instance
        for the given model instance.
    """

    if not obj:
        return False

    return ContentType.objects.get_for_model(obj)


@register.filter
def user_is_admin(user: User) -> bool:
    return user.is_superuser and user.groups.filter(name="Admins").exists()

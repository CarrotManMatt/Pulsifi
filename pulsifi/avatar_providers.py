""" Adapters for use in the pulsifi app. """
import abc
import math
from urllib import parse as urllib_parse_utils

from allauth.socialaccount.models import SocialAccount
from pulsifi.models import User


class Base_AvatarProvider(abc.ABC):
    """ Base abstract avatar URL provider class. """

    @classmethod
    @abc.abstractmethod
    def get_avatar_url(cls, user: User, width: int, height: int) -> str | None:
        """
            Returns the URL of this provider's avatar API, corresponding to
            the given user account.
        """

        raise NotImplementedError


class Sized_AvatarProvider(Base_AvatarProvider):
    """
        Base abstract avatar URL provider class for providers that use a "size"
        parameter in the API URL instead of width & height.
    """

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    @abc.abstractmethod
    def provider_name(cls) -> str:
        """
            The name of the provider that this avatar provider class will
            generate avatar URLs for.
        """

        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def calculate_size(width: int, height: int) -> int:
        """
            Returns the calculated size of the avatar image to request, from the
            given width & height.
        """

        raise NotImplementedError

    @staticmethod
    def generate_sized_url(url: str, size):
        """
            Returns the given URL with the size argument added as a URL
            parameter.
        """

        if "?" not in url:
            return f"{url}?size={size}"
        elif "size=" not in url:
            return f"{url}&size={size}"
        else:
            parsed_url = urllib_parse_utils.urlsplit(url)
            url_parameters: dict[str, list[str]] = urllib_parse_utils.parse_qs(
                parsed_url.query, strict_parsing=True
            )

            url_parameters["size"] = [size]

            return urllib_parse_utils.urlunsplit(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    urllib_parse_utils.urlencode(url_parameters),
                    parsed_url.fragment
                )
            )

    @classmethod
    def get_avatar_url(cls, user: User, width: int, height: int) -> str | None:
        """
            Returns the URL of this provider's avatar API, corresponding to
            the given user account.
        """

        try:
            social_account: SocialAccount = user.socialaccount_set.get(
                provider=cls.provider_name
            )
        except SocialAccount.DoesNotExist:
            return
        else:
            return cls.generate_sized_url(
                social_account.get_avatar_url(),
                cls.calculate_size(width, height)
            )


class DiscordAvatarProvider(Sized_AvatarProvider):
    """ Avatar URL provider for when users have linked a Discord account. """

    provider_name = "discord"

    @staticmethod
    def calculate_size(width: int, height: int) -> int:
        """
            Returns the calculated size of the avatar image to request, from the
            given width & height.
        """

        size = 1 << (int(math.sqrt(width * height)) - 1).bit_length()

        if size < 1 or width < 1 or height < 1:
            raise ValueError("Given width & height must be within the valid range so that the calculated size is greater than 0.")

        if size > 4096:
            return 4096
        elif size < 16:
            return 16
        else:
            return size


class GithubAvatarProvider(Sized_AvatarProvider):
    """ Avatar URL provider for when users have linked a GitHub account. """

    provider_name = "github"

    @staticmethod
    def calculate_size(width: int, height: int) -> int:
        """
            Returns the calculated size of the avatar image to request, from the
            given width & height.
        """

        size: int = int(math.sqrt(width * height))

        if size < 1 or width < 1 or height < 1:
            raise ValueError("Given width & height must be within the valid range so that the calculated size is greater than 0.")

        if size > 460:
            return 460
        else:
            return size


class GoogleAvatarProvider(Base_AvatarProvider):
    """ Avatar URL provider for when users have linked a Google account. """

    @classmethod
    def get_avatar_url(cls, user: User, width: int, height: int) -> str | None:
        """
            Returns the URL of Google's avatar API, corresponding to this
            account.
        """

        if width < 1 or height < 1:
            raise ValueError("Given width & height must be greater than 0.")

        try:
            google_social_account: SocialAccount = user.socialaccount_set.get(provider="google")
        except SocialAccount.DoesNotExist:
            return
        else:
            return f"""{google_social_account.get_avatar_url().rpartition("=")[0]}=w{width}-h{height}-c"""

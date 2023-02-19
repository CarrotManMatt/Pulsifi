""" Adapters for use in the pulsifi app. """

from allauth.socialaccount.models import SocialAccount

from pulsifi.models import User


class DiscordAvatarProvider:
    @staticmethod
    def get_avatar_url(user: User, width: int, height: int) -> str | None:
        size = 1 << (int((width * height) / 2) - 1).bit_length()
        if size > 4096:
            size = 4096
        elif size < 16:
            size = 16

        try:
            discord_SocialAccount: SocialAccount = user.socialaccount_set.get(provider="discord")
        except SocialAccount.DoesNotExist:
            return
        else:
            return f"{discord_SocialAccount.get_avatar_url()}?size={size}"


class GithubAvatarProvider:
    @staticmethod
    def get_avatar_url(user: User, width: int, height: int) -> str | None:
        size = int((width * height) / 2)
        if size > 460:
            size = 460
        elif size < 8:
            size = 8

        try:
            github_SocialAccount: SocialAccount = user.socialaccount_set.get(provider="github")
        except SocialAccount.DoesNotExist:
            return
        else:
            return f"{github_SocialAccount.get_avatar_url()}?size={size}"

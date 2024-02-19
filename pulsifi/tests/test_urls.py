"""
    Automated test suite for URLs in core app & pulsifi app.
"""

from django import urls
from django.views import View
from pulsifi import views
from pulsifi.tests.utils import Base_TestCase, Test_User_Factory


class Pulsifi_Url_Patterns_Tests(Base_TestCase):
    def test_url_maps_to_correct_view(self):
        url: str
        view: View
        for url, view in {("home", views.Home_View), ("feed", views.Feed_View), ("self_account", views.Self_Account_View), ("following", views.Following_View), ("followers", views.Followers_View), ("signup_POST", views.Signup_POST_View), ("login_POST", views.Login_POST_View)}:
            self.assertEqual(
                urls.resolve(urls.reverse(f"pulsifi:{url}")).func.view_class,
                view
            )

        self.assertEqual(
            urls.resolve(
                urls.reverse(
                    "pulsifi:specific_account",
                    kwargs={
                        "username": Test_User_Factory.create_field_value(
                            "username"
                        )
                    }
                )
            ).func.view_class,
            views.Specific_Account_View
        )


class Core_Url_Patterns_Tests(Base_TestCase):
    def test_url_maps_to_correct_view(self):
        self.assertEqual(
            self.client.get(urls.reverse("default"), follow=True).status_code,
            200
        )

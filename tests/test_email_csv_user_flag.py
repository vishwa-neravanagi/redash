from tests import BaseTestCase


class TestEmailExportEnabledFlag(BaseTestCase):
    def test_default_is_false(self):
        user = self.factory.user
        self.assertFalse(user.email_export_enabled)

    def test_to_dict_includes_flag(self):
        user = self.factory.user
        d = user.to_dict()
        self.assertIn("email_export_enabled", d)
        self.assertFalse(d["email_export_enabled"])

    def test_admin_can_set_flag(self):
        admin = self.factory.create_admin()
        user = self.factory.create_user()

        rv = self.make_request(
            "post",
            "/api/users/{}".format(user.id),
            user=admin,
            data={"email_export_enabled": True},
        )
        self.assertEqual(200, rv.status_code)
        self.assertTrue(rv.json["email_export_enabled"])

    def test_non_admin_cannot_set_flag_on_other_user(self):
        user = self.factory.create_user()
        other_user = self.factory.create_user()

        rv = self.make_request(
            "post",
            "/api/users/{}".format(other_user.id),
            user=user,
            data={"email_export_enabled": True},
        )
        self.assertEqual(403, rv.status_code)

    def test_non_admin_cannot_set_own_flag(self):
        user = self.factory.create_user()

        rv = self.make_request(
            "post",
            "/api/users/{}".format(user.id),
            user=user,
            data={"email_export_enabled": True},
        )
        self.assertEqual(403, rv.status_code)

    def test_session_includes_flag(self):
        user = self.factory.user
        rv = self.make_request("get", "/api/session")
        self.assertIn("email_export_enabled", rv.json["user"])

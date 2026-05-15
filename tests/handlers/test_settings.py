from redash.models import Organization, db
from tests import BaseTestCase


class TestOrganizationSettings(BaseTestCase):
    def test_post(self):
        admin = self.factory.create_admin()
        rv = self.make_request(
            "post",
            "/api/settings/organization",
            data={"auth_password_login_enabled": False},
            user=admin,
        )
        self.assertEqual(rv.json["settings"]["auth_password_login_enabled"], False)
        self.assertEqual(self.factory.org.settings["settings"]["auth_password_login_enabled"], False)

        rv = self.make_request(
            "post",
            "/api/settings/organization",
            data={"auth_password_login_enabled": True},
            user=admin,
        )
        updated_org = Organization.get_by_slug(self.factory.org.slug)
        self.assertEqual(rv.json["settings"]["auth_password_login_enabled"], True)
        self.assertEqual(updated_org.settings["settings"]["auth_password_login_enabled"], True)

    def test_updates_google_apps_domains(self):
        admin = self.factory.create_admin()
        domains = ["example.com"]
        self.make_request(
            "post",
            "/api/settings/organization",
            data={"auth_google_apps_domains": domains},
            user=admin,
        )
        updated_org = Organization.get_by_slug(self.factory.org.slug)
        self.assertEqual(updated_org.google_apps_domains, domains)

    def test_get_returns_google_appas_domains(self):
        admin = self.factory.create_admin()
        domains = ["example.com"]
        admin.org.settings[Organization.SETTING_GOOGLE_APPS_DOMAINS] = domains

        rv = self.make_request("get", "/api/settings/organization", user=admin)
        self.assertEqual(rv.json["settings"]["auth_google_apps_domains"], domains)


class TestEmailCsvOrgSettings(BaseTestCase):
    def test_get_returns_email_csv_defaults(self):
        admin = self.factory.create_admin()
        rv = self.make_request("get", "/api/settings/organization", user=admin)
        self.assertEqual(rv.json["settings"]["email_csv_cooldown_seconds"], 30)
        self.assertEqual(rv.json["settings"]["email_csv_max_attachment_size_mb"], 25)
        self.assertEqual(rv.json["settings"]["s3_email_export_link_mode"], False)
        self.assertEqual(rv.json["settings"]["s3_email_export_link_expiry_seconds"], 86400)

    def test_post_email_csv_cooldown(self):
        admin = self.factory.create_admin()
        rv = self.make_request(
            "post",
            "/api/settings/organization",
            data={"email_csv_cooldown_seconds": 60},
            user=admin,
        )
        self.assertEqual(rv.json["settings"]["email_csv_cooldown_seconds"], 60)

    def test_post_s3_email_export_settings(self):
        admin = self.factory.create_admin()
        rv = self.make_request(
            "post",
            "/api/settings/organization",
            data={
                "s3_email_export_bucket": "my-bucket",
                "s3_email_export_region": "us-west-2",
                "s3_email_export_link_mode": True,
            },
            user=admin,
        )
        self.assertEqual(rv.json["settings"]["s3_email_export_bucket"], "my-bucket")
        self.assertEqual(rv.json["settings"]["s3_email_export_region"], "us-west-2")
        self.assertEqual(rv.json["settings"]["s3_email_export_link_mode"], True)

    def test_org_setting_overrides_default(self):
        admin = self.factory.create_admin()
        self.make_request(
            "post",
            "/api/settings/organization",
            data={"email_csv_max_attachment_size_mb": 10},
            user=admin,
        )
        self.assertEqual(
            self.factory.org.get_setting("email_csv_max_attachment_size_mb"), 10
        )

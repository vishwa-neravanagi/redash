from unittest.mock import patch

from tests import BaseTestCase
from redash.models import db
from redash.tasks.email_csv import email_csv_task


class TestEmailCsvTask(BaseTestCase):
    @patch("redash.tasks.email_csv.mail")
    def test_sends_email_with_csv_attachment(self, mock_mail):
        query_result = self.factory.create_query_result()
        query = self.factory.create_query(latest_query_data=query_result)
        user = self.factory.user

        email_csv_task(
            result_id=query_result.id,
            query_id=query.id,
            query_name=query.name,
            user_email=user.email,
            file_extension="csv",
            note=None,
            org_id=self.factory.org.id,
        )

        mock_mail.send.assert_called_once()
        message = mock_mail.send.call_args[0][0]
        self.assertEqual(message.recipients, [user.email])
        self.assertEqual(len(message.attachments), 1)
        self.assertTrue(message.attachments[0].filename.endswith(".csv"))

    @patch("redash.tasks.email_csv.mail")
    def test_sends_email_with_note_in_body(self, mock_mail):
        query_result = self.factory.create_query_result()
        query = self.factory.create_query(latest_query_data=query_result)
        user = self.factory.user

        email_csv_task(
            result_id=query_result.id,
            query_id=query.id,
            query_name=query.name,
            user_email=user.email,
            file_extension="csv",
            note="Please review this data",
            org_id=self.factory.org.id,
        )

        message = mock_mail.send.call_args[0][0]
        self.assertIn("Please review this data", message.body)

    @patch("redash.tasks.email_csv.mail")
    @patch("redash.tasks.email_csv._upload_to_s3")
    def test_uploads_to_s3_when_configured(self, mock_s3, mock_mail):
        self.factory.org.set_setting("s3_email_export_bucket", "test-bucket")
        self.factory.org.set_setting("s3_email_export_prefix", "exports/")
        db.session.commit()

        query_result = self.factory.create_query_result()
        query = self.factory.create_query(latest_query_data=query_result)
        user = self.factory.user

        email_csv_task(
            result_id=query_result.id,
            query_id=query.id,
            query_name=query.name,
            user_email=user.email,
            file_extension="csv",
            note=None,
            org_id=self.factory.org.id,
        )

        mock_s3.assert_called_once()

    @patch("redash.tasks.email_csv.mail")
    def test_link_mode_sends_url_instead_of_attachment(self, mock_mail):
        self.factory.org.set_setting("s3_email_export_bucket", "test-bucket")
        self.factory.org.set_setting("s3_email_export_prefix", "exports/")
        self.factory.org.set_setting("s3_email_export_link_mode", True)
        self.factory.org.set_setting("s3_email_export_link_expiry_seconds", 3600)
        db.session.commit()

        with patch("redash.tasks.email_csv._upload_to_s3") as mock_s3:
            mock_s3.return_value = "https://test-bucket.s3.amazonaws.com/exports/file.csv"

            query_result = self.factory.create_query_result()
            query = self.factory.create_query(latest_query_data=query_result)
            user = self.factory.user

            email_csv_task(
                result_id=query_result.id,
                query_id=query.id,
                query_name=query.name,
                user_email=user.email,
                file_extension="csv",
                note=None,
                org_id=self.factory.org.id,
            )

            message = mock_mail.send.call_args[0][0]
            self.assertEqual(len(message.attachments), 0)
            self.assertIn("https://", message.body)

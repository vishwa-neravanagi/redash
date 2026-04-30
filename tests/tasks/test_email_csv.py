from unittest.mock import patch

from tests import BaseTestCase
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
        )

        message = mock_mail.send.call_args[0][0]
        self.assertIn("Please review this data", message.body)

    @patch("redash.tasks.email_csv.mail")
    @patch("redash.tasks.email_csv._upload_to_s3")
    def test_uploads_to_s3_when_configured(self, mock_s3, mock_mail):
        with patch("redash.tasks.email_csv.settings") as mock_settings:
            mock_settings.S3_EMAIL_EXPORT_BUCKET = "test-bucket"
            mock_settings.S3_EMAIL_EXPORT_PREFIX = "exports/"
            mock_settings.S3_EMAIL_EXPORT_ACCESS_KEY = None
            mock_settings.S3_EMAIL_EXPORT_SECRET_KEY = None
            mock_settings.S3_EMAIL_EXPORT_REGION = None
            mock_settings.S3_EMAIL_EXPORT_LINK_MODE = False
            mock_settings.S3_EMAIL_EXPORT_LINK_EXPIRY_SECONDS = 86400

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
            )

            mock_s3.assert_called_once()

    @patch("redash.tasks.email_csv.mail")
    def test_link_mode_sends_url_instead_of_attachment(self, mock_mail):
        with patch("redash.tasks.email_csv.settings") as mock_settings:
            mock_settings.S3_EMAIL_EXPORT_BUCKET = "test-bucket"
            mock_settings.S3_EMAIL_EXPORT_PREFIX = "exports/"
            mock_settings.S3_EMAIL_EXPORT_ACCESS_KEY = None
            mock_settings.S3_EMAIL_EXPORT_SECRET_KEY = None
            mock_settings.S3_EMAIL_EXPORT_REGION = None
            mock_settings.S3_EMAIL_EXPORT_LINK_MODE = True
            mock_settings.S3_EMAIL_EXPORT_LINK_EXPIRY_SECONDS = 3600

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
                )

                message = mock_mail.send.call_args[0][0]
                self.assertEqual(len(message.attachments), 0)
                self.assertIn("https://", message.body)

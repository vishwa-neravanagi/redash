from unittest.mock import patch

from tests import BaseTestCase
from redash.models import db


class TestEmailCsvEndpoint(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.query_result = self.factory.create_query_result()
        self.query = self.factory.create_query(latest_query_data=self.query_result)
        self.factory.user.email_export_enabled = True
        db.session.commit()

    @patch("redash.handlers.email_csv.email_csv_task")
    def test_successful_email_csv(self, mock_task):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "immediate"},
        )
        self.assertEqual(200, rv.status_code)
        self.assertIn("message", rv.json)
        mock_task.delay.assert_called_once()

    @patch("redash.handlers.email_csv.email_csv_task")
    def test_email_csv_with_note(self, mock_task):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "with_note", "note": "Check this out"},
        )
        self.assertEqual(200, rv.status_code)
        call_kwargs = mock_task.delay.call_args[1]
        self.assertEqual(call_kwargs["note"], "Check this out")

    def test_returns_403_when_flag_disabled(self):
        self.factory.user.email_export_enabled = False
        db.session.commit()
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "immediate"},
        )
        self.assertEqual(403, rv.status_code)

    def test_returns_400_for_invalid_file_extension(self):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/pdf".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "immediate"},
        )
        self.assertEqual(400, rv.status_code)

    def test_returns_400_for_invalid_method(self):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "invalid"},
        )
        self.assertEqual(400, rv.status_code)

    def test_returns_400_for_note_too_long(self):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "with_note", "note": "x" * 1001},
        )
        self.assertEqual(400, rv.status_code)

    def test_returns_404_for_invalid_result_id(self):
        rv = self.make_request(
            "post",
            "/api/query_results/99999/email/csv",
            data={"query_id": self.query.id, "method": "immediate"},
        )
        self.assertEqual(404, rv.status_code)

    @patch("redash.handlers.email_csv.email_csv_task")
    def test_adhoc_query_works(self, mock_task):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": None, "method": "immediate"},
        )
        self.assertEqual(200, rv.status_code)
        mock_task.delay.assert_called_once()

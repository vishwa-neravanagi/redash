from unittest.mock import patch

from tests import BaseTestCase
from redash.models import db


class TestEmailCsvIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.query_result = self.factory.create_query_result()
        self.query = self.factory.create_query(latest_query_data=self.query_result)
        self.factory.user.email_export_enabled = True
        db.session.commit()

    @patch("redash.handlers.email_csv.email_csv_task")
    def test_event_is_recorded(self, mock_task):
        rv = self.make_request(
            "post",
            "/api/query_results/{}/email/csv".format(self.query_result.id),
            data={"query_id": self.query.id, "method": "immediate"},
        )
        self.assertEqual(200, rv.status_code)

    @patch("redash.handlers.email_csv.email_csv_task")
    def test_all_three_methods_work(self, mock_task):
        for method in ["immediate", "confirmed", "with_note"]:
            data = {"query_id": self.query.id, "method": method}
            if method == "with_note":
                data["note"] = "Test note"

            rv = self.make_request(
                "post",
                "/api/query_results/{}/email/csv".format(self.query_result.id),
                data=data,
            )
            self.assertEqual(200, rv.status_code)

    @patch("redash.handlers.email_csv.email_csv_task")
    def test_tsv_and_xlsx_extensions(self, mock_task):
        for ext in ["tsv", "xlsx"]:
            rv = self.make_request(
                "post",
                "/api/query_results/{}/email/{}".format(self.query_result.id, ext),
                data={"query_id": self.query.id, "method": "immediate"},
            )
            self.assertEqual(200, rv.status_code)

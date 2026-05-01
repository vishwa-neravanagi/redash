import time

from flask import request
from flask_restful import abort

from redash import models, settings
from redash.handlers.base import BaseResource, get_object_or_404, record_event
from redash.permissions import require_access, view_only
from redash.serializers import serialize_query_result_to_dsv, serialize_query_result_to_xlsx
from redash.tasks.email_csv import email_csv_task

VALID_FILE_EXTENSIONS = {"csv", "tsv", "xlsx"}
VALID_METHODS = {"immediate", "confirmed", "with_note"}
MAX_NOTE_LENGTH = 1000


class QueryResultEmailResource(BaseResource):
    def post(self, query_result_id, file_extension):
        if file_extension not in VALID_FILE_EXTENSIONS:
            abort(400, message=f"Invalid file extension. Must be one of: {', '.join(VALID_FILE_EXTENSIONS)}")

        if not self.current_user.email_export_enabled:
            abort(403, message="Email export is not enabled for your account.")

        query_result = get_object_or_404(
            models.QueryResult.get_by_id_and_org, query_result_id, self.current_org
        )

        require_access(query_result.data_source, self.current_user, view_only)

        req = request.get_json(force=True)
        method = req.get("method", "")
        if method not in VALID_METHODS:
            abort(400, message=f"Invalid method. Must be one of: {', '.join(VALID_METHODS)}")

        note = req.get("note")
        if note and len(note) > MAX_NOTE_LENGTH:
            abort(400, message=f"Note must be {MAX_NOTE_LENGTH} characters or fewer.")

        query_id = req.get("query_id")
        query_name = None
        if query_id:
            query = models.Query.query.get(query_id)
            if query:
                query_name = query.name

        # Size check (only in non-link mode)
        if not settings.S3_EMAIL_EXPORT_LINK_MODE:
            if file_extension in ("csv", "tsv"):
                delimiter = "," if file_extension == "csv" else "\t"
                file_data = serialize_query_result_to_dsv(query_result, delimiter).encode("utf-8")
            else:
                file_data = serialize_query_result_to_xlsx(query_result)

            max_size_bytes = settings.EMAIL_CSV_MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
            if len(file_data) > max_size_bytes:
                abort(413, message=f"File size exceeds maximum of {settings.EMAIL_CSV_MAX_ATTACHMENT_SIZE_MB} MB.")

        # Build filename for event logging
        timestamp_ns = time.time_ns()
        safe_name = (query_name or "Adhoc_Query").replace(" ", "_")
        qid = str(query_id) if query_id else "adhoc"
        filename = f"{safe_name}_{timestamp_ns}_{qid}_{query_result_id}.{file_extension}"

        # S3 path (intended)
        s3_path = None
        if settings.S3_EMAIL_EXPORT_BUCKET:
            s3_path = f"s3://{settings.S3_EMAIL_EXPORT_BUCKET}/{settings.S3_EMAIL_EXPORT_PREFIX}{filename}"

        # Record event
        record_event(
            self.current_org,
            self.current_user,
            {
                "action": "email_csv",
                "object_type": "query_result",
                "object_id": str(query_result_id),
                "query_id": query_id,
                "email_to": self.current_user.email,
                "method": method,
                "note": note,
                "file_extension": file_extension,
                "filename": filename,
                "s3_path": s3_path,
            },
        )

        # Dispatch RQ job
        email_csv_task.delay(
            result_id=query_result_id,
            query_id=query_id,
            query_name=query_name,
            user_email=self.current_user.email,
            file_extension=file_extension,
            note=note,
            filename=filename,
        )

        return {"message": "Email queued successfully."}

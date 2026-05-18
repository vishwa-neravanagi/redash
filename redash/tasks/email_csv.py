import time

import boto3
from flask_mail import Message

from redash import mail, models
from redash.app import create_app
from redash.models import db
from redash.serializers import serialize_query_result_to_dsv, serialize_query_result_to_xlsx
from redash.worker import get_job_logger, job

logger = get_job_logger(__name__)

CONTENT_TYPES = {
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _build_filename(query_name, query_id, result_id, file_extension):
    timestamp_ns = time.time_ns()
    safe_name = query_name.replace(" ", "_") if query_name else "Adhoc_Query"
    qid = str(query_id) if query_id else "adhoc"
    return f"{safe_name}_{timestamp_ns}_{qid}_{result_id}.{file_extension}"


def _generate_file_data(query_result, file_extension):
    if file_extension in ("csv", "tsv"):
        delimiter = "," if file_extension == "csv" else "\t"
        return serialize_query_result_to_dsv(query_result, delimiter).encode("utf-8")
    elif file_extension == "xlsx":
        return serialize_query_result_to_xlsx(query_result)


def _get_s3_client(org):
    kwargs = {}
    access_key = org.get_setting("s3_email_export_access_key")
    secret_key = org.get_setting("s3_email_export_secret_key")
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
    region = org.get_setting("s3_email_export_region")
    if region:
        kwargs["region_name"] = region
    return boto3.client("s3", **kwargs)


def _upload_to_s3(filename, file_data, content_type, org):
    s3 = _get_s3_client(org)
    prefix = org.get_setting("s3_email_export_prefix")
    bucket = org.get_setting("s3_email_export_bucket")
    key = f"{prefix}{filename}"
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_data,
        ContentType=content_type,
    )

    if org.get_setting("s3_email_export_link_mode"):
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=org.get_setting("s3_email_export_link_expiry_seconds"),
        )
        return presigned_url

    return f"s3://{bucket}/{key}"


@job("emails")
def email_csv_task(result_id, query_id, query_name, user_email, file_extension, note, filename=None, org_id=None):
    try:
        query_result = db.session.get(models.QueryResult, result_id)
        if not query_result:
            logger.error("QueryResult %s not found", result_id)
            return

        org = models.Organization.get_by_id(org_id) if org_id else None

        if not filename:
            filename = _build_filename(query_name, query_id, result_id, file_extension)
        file_data = _generate_file_data(query_result, file_extension)
        content_type = CONTENT_TYPES.get(file_extension, "application/octet-stream")

        subject = f"Redash: CSV export — {filename}"

        body_parts = []
        if note:
            body_parts.append(note)
            body_parts.append("")
        body_parts.append(f"Query: {query_name or 'Adhoc Query'}")
        body_parts.append(f"Exported at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

        s3_url = None
        s3_bucket = org.get_setting("s3_email_export_bucket") if org else ""
        link_mode = org.get_setting("s3_email_export_link_mode") if org else False
        if s3_bucket:
            try:
                s3_url = _upload_to_s3(filename, file_data, content_type, org)
            except Exception:
                logger.exception("Failed to upload %s to S3", filename)

        if link_mode and s3_url and s3_url.startswith("https://"):
            link_expiry = org.get_setting("s3_email_export_link_expiry_seconds") if org else 86400
            body_parts.append("")
            if link_expiry >= 3600:
                expiry_display = f"{link_expiry // 3600} hours"
            else:
                expiry_display = f"{link_expiry // 60} minutes"
            body_parts.append(f"Download link (expires in {expiry_display}):")
            body_parts.append(s3_url)

            message = Message(
                recipients=[user_email],
                subject=subject,
                body="\n".join(body_parts),
            )
        else:
            message = Message(
                recipients=[user_email],
                subject=subject,
                body="\n".join(body_parts),
            )
            message.attach(filename, content_type, file_data)

        app = create_app()
        with app.app_context():
            mail.send(message)
    except Exception:
        logger.exception("Failed to send email CSV export to %s", user_email)

import time

import boto3
from flask_mail import Message

from redash import mail, models, settings
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


def _get_s3_client():
    kwargs = {}
    if settings.S3_EMAIL_EXPORT_ACCESS_KEY and settings.S3_EMAIL_EXPORT_SECRET_KEY:
        kwargs["aws_access_key_id"] = settings.S3_EMAIL_EXPORT_ACCESS_KEY
        kwargs["aws_secret_access_key"] = settings.S3_EMAIL_EXPORT_SECRET_KEY
    if settings.S3_EMAIL_EXPORT_REGION:
        kwargs["region_name"] = settings.S3_EMAIL_EXPORT_REGION
    return boto3.client("s3", **kwargs)


def _upload_to_s3(filename, file_data, content_type):
    s3 = _get_s3_client()
    key = f"{settings.S3_EMAIL_EXPORT_PREFIX}{filename}"
    s3.put_object(
        Bucket=settings.S3_EMAIL_EXPORT_BUCKET,
        Key=key,
        Body=file_data,
        ContentType=content_type,
    )

    if settings.S3_EMAIL_EXPORT_LINK_MODE:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_EMAIL_EXPORT_BUCKET, "Key": key},
            ExpiresIn=settings.S3_EMAIL_EXPORT_LINK_EXPIRY_SECONDS,
        )
        return presigned_url

    return f"s3://{settings.S3_EMAIL_EXPORT_BUCKET}/{key}"


@job("emails")
def email_csv_task(result_id, query_id, query_name, user_email, file_extension, note, filename=None):
    try:
        query_result = db.session.get(models.QueryResult, result_id)
        if not query_result:
            logger.error("QueryResult %s not found", result_id)
            return

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
        if settings.S3_EMAIL_EXPORT_BUCKET:
            try:
                s3_url = _upload_to_s3(filename, file_data, content_type)
            except Exception:
                logger.exception("Failed to upload %s to S3", filename)

        if settings.S3_EMAIL_EXPORT_LINK_MODE and s3_url and s3_url.startswith("https://"):
            body_parts.append("")
            body_parts.append(f"Download link (expires in {settings.S3_EMAIL_EXPORT_LINK_EXPIRY_SECONDS // 3600} hours):")
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

        mail.send(message)
    except Exception:
        logger.exception("Failed to send email CSV export to %s", user_email)

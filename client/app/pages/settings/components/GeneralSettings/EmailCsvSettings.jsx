import React from "react";
import Form from "antd/lib/form";
import Input from "antd/lib/input";
import InputNumber from "antd/lib/input-number";
import Checkbox from "antd/lib/checkbox";
import Skeleton from "antd/lib/skeleton";
import DynamicComponent from "@/components/DynamicComponent";
import { SettingsEditorPropTypes, SettingsEditorDefaultProps } from "../prop-types";

export default function EmailCsvSettings(props) {
  const { values, onChange, loading } = props;

  return (
    <DynamicComponent name="OrganizationSettings.EmailCsvSettings" {...props}>
      <h4>Email CSV Export</h4>

      <Form.Item label="Cooldown Between Emails (seconds)">
        {loading ? (
          <Skeleton.Input style={{ width: 200 }} active />
        ) : (
          <InputNumber
            min={0}
            value={values.email_csv_cooldown_seconds}
            onChange={value => onChange({ email_csv_cooldown_seconds: value })}
          />
        )}
      </Form.Item>

      <Form.Item label="Max Attachment Size (MB)">
        {loading ? (
          <Skeleton.Input style={{ width: 200 }} active />
        ) : (
          <InputNumber
            min={1}
            value={values.email_csv_max_attachment_size_mb}
            onChange={value => onChange({ email_csv_max_attachment_size_mb: value })}
          />
        )}
      </Form.Item>

      <h4>S3 Storage for Email Exports</h4>

      <Form.Item label="S3 Bucket">
        {loading ? (
          <Skeleton.Input style={{ width: 300 }} active />
        ) : (
          <Input
            value={values.s3_email_export_bucket || ""}
            onChange={e => onChange({ s3_email_export_bucket: e.target.value })}
            placeholder="my-bucket"
          />
        )}
      </Form.Item>

      <Form.Item label="S3 Key Prefix">
        {loading ? (
          <Skeleton.Input style={{ width: 300 }} active />
        ) : (
          <Input
            value={values.s3_email_export_prefix || ""}
            onChange={e => onChange({ s3_email_export_prefix: e.target.value })}
            placeholder="redash-csv-exports/"
          />
        )}
      </Form.Item>

      <Form.Item label="S3 Access Key">
        {loading ? (
          <Skeleton.Input style={{ width: 300 }} active />
        ) : (
          <Input
            value={values.s3_email_export_access_key || ""}
            onChange={e => onChange({ s3_email_export_access_key: e.target.value })}
          />
        )}
      </Form.Item>

      <Form.Item label="S3 Secret Key">
        {loading ? (
          <Skeleton.Input style={{ width: 300 }} active />
        ) : (
          <Input.Password
            value={values.s3_email_export_secret_key || ""}
            onChange={e => onChange({ s3_email_export_secret_key: e.target.value })}
          />
        )}
      </Form.Item>

      <Form.Item label="S3 Region">
        {loading ? (
          <Skeleton.Input style={{ width: 300 }} active />
        ) : (
          <Input
            value={values.s3_email_export_region || ""}
            onChange={e => onChange({ s3_email_export_region: e.target.value })}
            placeholder="us-east-1"
          />
        )}
      </Form.Item>

      <Form.Item>
        <Checkbox
          checked={values.s3_email_export_link_mode}
          disabled={loading}
          onChange={e => onChange({ s3_email_export_link_mode: e.target.checked })}>
          Send pre-signed S3 links instead of attachments
        </Checkbox>
      </Form.Item>

      {values.s3_email_export_link_mode && (
        <Form.Item label="Link Expiry (seconds)">
          {loading ? (
            <Skeleton.Input style={{ width: 200 }} active />
          ) : (
            <InputNumber
              min={60}
              value={values.s3_email_export_link_expiry_seconds}
              onChange={value => onChange({ s3_email_export_link_expiry_seconds: value })}
            />
          )}
        </Form.Item>
      )}
    </DynamicComponent>
  );
}

EmailCsvSettings.propTypes = SettingsEditorPropTypes;

EmailCsvSettings.defaultProps = SettingsEditorDefaultProps;

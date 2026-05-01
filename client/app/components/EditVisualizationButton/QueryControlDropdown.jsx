import React, { useState, useCallback, useRef } from "react";
import PropTypes from "prop-types";
import Dropdown from "antd/lib/dropdown";
import Menu from "antd/lib/menu";
import Button from "antd/lib/button";
import notification from "antd/lib/notification";
import PlainButton from "@/components/PlainButton";
import { currentUser, clientConfig } from "@/services/auth";
import { axios } from "@/services/axios";

import PlusCircleFilledIcon from "@ant-design/icons/PlusCircleFilled";
import ShareAltOutlinedIcon from "@ant-design/icons/ShareAltOutlined";
import FileOutlinedIcon from "@ant-design/icons/FileOutlined";
import FileExcelOutlinedIcon from "@ant-design/icons/FileExcelOutlined";
import EllipsisOutlinedIcon from "@ant-design/icons/EllipsisOutlined";
import MailOutlinedIcon from "@ant-design/icons/MailOutlined";

import QueryResultsLink from "./QueryResultsLink";
import { EmailCsvConfirmModal, EmailCsvWithNoteModal } from "./EmailCsvModal";

function sendEmailCsv(queryResult, query, method, note = null) {
  const resultId = queryResult.getId ? queryResult.getId() : queryResult.id;
  const queryId = query && !query.isNew() ? query.id : null;

  return axios.post(`api/query_results/${resultId}/email/csv`, {
    query_id: queryId,
    method,
    note,
  });
}

export default function QueryControlDropdown(props) {
  const [confirmModalVisible, setConfirmModalVisible] = useState(false);
  const [noteModalVisible, setNoteModalVisible] = useState(false);
  const [cooldown, setCooldown] = useState(false);
  const cooldownTimer = useRef(null);

  const cooldownSeconds = clientConfig.emailCsvCooldownSeconds || 30;
  const emailEnabled = currentUser.email_export_enabled;
  const isDisabled = props.queryExecuting || !props.queryResult.getData || !props.queryResult.getData();

  const startCooldown = useCallback(() => {
    setCooldown(true);
    if (cooldownTimer.current) clearTimeout(cooldownTimer.current);
    cooldownTimer.current = setTimeout(() => setCooldown(false), cooldownSeconds * 1000);
  }, [cooldownSeconds]);

  const handleEmailImmediate = useCallback(() => {
    sendEmailCsv(props.queryResult, props.query, "immediate")
      .then(() => {
        notification.success({ message: `CSV emailed to ${currentUser.email}` });
        startCooldown();
      })
      .catch(() => {
        notification.error({ message: "Failed to send email" });
      });
  }, [props.queryResult, props.query, startCooldown]);

  const handleEmailConfirm = useCallback(() => {
    sendEmailCsv(props.queryResult, props.query, "confirmed")
      .then(() => {
        notification.success({ message: `CSV emailed to ${currentUser.email}` });
        startCooldown();
      })
      .catch(() => {
        notification.error({ message: "Failed to send email" });
      });
    setConfirmModalVisible(false);
  }, [props.queryResult, props.query, startCooldown]);

  const handleEmailWithNote = useCallback(
    note => {
      sendEmailCsv(props.queryResult, props.query, "with_note", note)
        .then(() => {
          notification.success({ message: `CSV emailed to ${currentUser.email}` });
          startCooldown();
        })
        .catch(() => {
          notification.error({ message: "Failed to send email" });
        });
      setNoteModalVisible(false);
    },
    [props.queryResult, props.query, startCooldown]
  );

  const menu = (
    <Menu>
      {!props.query.isNew() && (!props.query.is_draft || !props.query.is_archived) && (
        <Menu.Item>
          <PlainButton onClick={() => props.openAddToDashboardForm(props.selectedTab)}>
            <PlusCircleFilledIcon /> Add to Dashboard
          </PlainButton>
        </Menu.Item>
      )}
      {!clientConfig.disablePublicUrls && !props.query.isNew() && (
        <Menu.Item>
          <PlainButton
            onClick={() => props.showEmbedDialog(props.query, props.selectedTab)}
            data-test="ShowEmbedDialogButton">
            <ShareAltOutlinedIcon /> Embed Elsewhere
          </PlainButton>
        </Menu.Item>
      )}
      <Menu.Item>
        <QueryResultsLink
          fileType="csv"
          disabled={isDisabled}
          query={props.query}
          queryResult={props.queryResult}
          embed={props.embed}
          apiKey={props.apiKey}>
          <FileOutlinedIcon /> Download as CSV File
        </QueryResultsLink>
      </Menu.Item>
      <Menu.Item>
        <QueryResultsLink
          fileType="tsv"
          disabled={isDisabled}
          query={props.query}
          queryResult={props.queryResult}
          embed={props.embed}
          apiKey={props.apiKey}>
          <FileOutlinedIcon /> Download as TSV File
        </QueryResultsLink>
      </Menu.Item>
      <Menu.Item>
        <QueryResultsLink
          fileType="xlsx"
          disabled={isDisabled}
          query={props.query}
          queryResult={props.queryResult}
          embed={props.embed}
          apiKey={props.apiKey}>
          <FileExcelOutlinedIcon /> Download as Excel File
        </QueryResultsLink>
      </Menu.Item>
      {emailEnabled && (
        <Menu.Item disabled={isDisabled || cooldown}>
          <PlainButton onClick={handleEmailImmediate} disabled={isDisabled || cooldown}>
            <MailOutlinedIcon /> Email CSV
          </PlainButton>
        </Menu.Item>
      )}
      {emailEnabled && (
        <Menu.Item disabled={isDisabled || cooldown}>
          <PlainButton onClick={() => setConfirmModalVisible(true)} disabled={isDisabled || cooldown}>
            <MailOutlinedIcon /> Email CSV (Confirm)
          </PlainButton>
        </Menu.Item>
      )}
      {emailEnabled && (
        <Menu.Item disabled={isDisabled || cooldown}>
          <PlainButton onClick={() => setNoteModalVisible(true)} disabled={isDisabled || cooldown}>
            <MailOutlinedIcon /> Email CSV (With Note)
          </PlainButton>
        </Menu.Item>
      )}
    </Menu>
  );

  return (
    <>
      <Dropdown trigger={["click"]} overlay={menu} overlayClassName="query-control-dropdown-overlay">
        <Button data-test="QueryControlDropdownButton">
          <EllipsisOutlinedIcon rotate={90} />
        </Button>
      </Dropdown>
      <EmailCsvConfirmModal
        visible={confirmModalVisible}
        onConfirm={handleEmailConfirm}
        onCancel={() => setConfirmModalVisible(false)}
        userEmail={currentUser.email}
      />
      <EmailCsvWithNoteModal
        visible={noteModalVisible}
        onConfirm={handleEmailWithNote}
        onCancel={() => setNoteModalVisible(false)}
        userEmail={currentUser.email}
      />
    </>
  );
}

QueryControlDropdown.propTypes = {
  query: PropTypes.object.isRequired,
  queryResult: PropTypes.object,
  queryExecuting: PropTypes.bool.isRequired,
  showEmbedDialog: PropTypes.func.isRequired,
  embed: PropTypes.bool,
  apiKey: PropTypes.string,
  selectedTab: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  openAddToDashboardForm: PropTypes.func.isRequired,
};

QueryControlDropdown.defaultProps = {
  queryResult: {},
  embed: false,
  apiKey: "",
  selectedTab: "",
};

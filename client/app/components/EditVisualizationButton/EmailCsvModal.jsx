import React, { useState } from "react";
import PropTypes from "prop-types";
import Modal from "antd/lib/modal";
import Input from "antd/lib/input";

const { TextArea } = Input;

export function EmailCsvConfirmModal({ visible, onConfirm, onCancel, userEmail }) {
  return (
    <Modal
      title="Email CSV"
      open={visible}
      onOk={onConfirm}
      onCancel={onCancel}
      okText="Send"
      cancelText="Cancel">
      <p>
        Email CSV to <strong>{userEmail}</strong>?
      </p>
    </Modal>
  );
}

EmailCsvConfirmModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  userEmail: PropTypes.string.isRequired,
};

export function EmailCsvWithNoteModal({ visible, onConfirm, onCancel, userEmail }) {
  const [note, setNote] = useState("");

  const handleConfirm = () => {
    onConfirm(note);
    setNote("");
  };

  const handleCancel = () => {
    setNote("");
    onCancel();
  };

  return (
    <Modal
      title="Email CSV with Note"
      open={visible}
      onOk={handleConfirm}
      onCancel={handleCancel}
      okText="Send"
      cancelText="Cancel">
      <p>
        Email CSV to <strong>{userEmail}</strong>
      </p>
      <TextArea
        rows={4}
        maxLength={1000}
        placeholder="Add an optional note..."
        value={note}
        onChange={e => setNote(e.target.value)}
      />
      <p style={{ marginTop: 8, color: "#999", fontSize: 12 }}>{note.length}/1000</p>
    </Modal>
  );
}

EmailCsvWithNoteModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  userEmail: PropTypes.string.isRequired,
};

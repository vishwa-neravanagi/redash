import React, { useState, useCallback } from "react";
import PropTypes from "prop-types";
import Switch from "antd/lib/switch";
import Form from "antd/lib/form";
import DynamicComponent from "@/components/DynamicComponent";
import { UserProfile } from "@/components/proptypes";
import { currentUser } from "@/services/auth";
import User from "@/services/user";
import useImmutableCallback from "@/lib/hooks/useImmutableCallback";

export default function EmailExportToggle(props) {
  const { user, onChange } = props;

  const [loading, setLoading] = useState(false);
  const handleChange = useImmutableCallback(onChange);

  const toggleEmailExport = useCallback(() => {
    setLoading(true);
    User.save({ id: user.id, email_export_enabled: !user.emailExportEnabled })
      .then(data => {
        if (data) {
          handleChange(User.convertUserInfo(data));
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [user, handleChange]);

  if (!currentUser.isAdmin || user.id === currentUser.id) {
    return null;
  }

  return (
    <DynamicComponent name="UserProfile.EmailExportToggle">
      <Form.Item label="Email CSV Export">
        <Switch
          checked={user.emailExportEnabled}
          onChange={toggleEmailExport}
          loading={loading}
        />
        <span className="m-l-10">{user.emailExportEnabled ? "Enabled" : "Disabled"}</span>
      </Form.Item>
    </DynamicComponent>
  );
}

EmailExportToggle.propTypes = {
  user: UserProfile.isRequired,
  onChange: PropTypes.func,
};

EmailExportToggle.defaultProps = {
  onChange: () => {},
};

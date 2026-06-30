import { Button, Card, Form, Input, message } from "antd";
import { api } from "../api";

export default function ChangePassword() {
  const [form] = Form.useForm();

  const onFinish = async (values: { old_password: string; new_password: string }) => {
    try {
      await api.post("/auth/change-password", values);
      message.success("密码已修改");
      form.resetFields();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "修改失败");
    }
  };

  return (
    <Card title="修改密码" style={{ width: "100%", maxWidth: 420 }}>
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item name="old_password" label="原密码" rules={[{ required: true }]}>
          <Input.Password size="large" />
        </Form.Item>
        <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6, message: "至少 6 位" }]}>
          <Input.Password size="large" />
        </Form.Item>
        <Button type="primary" htmlType="submit" size="large" block>
          保存
        </Button>
      </Form>
    </Card>
  );
}

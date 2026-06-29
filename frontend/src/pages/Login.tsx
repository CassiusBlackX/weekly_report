import { useState } from "react";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      navigate("/");
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
      }}
    >
      <Card style={{ width: 380, borderRadius: 16, boxShadow: "0 12px 40px rgba(0,0,0,0.2)" }}>
        <Typography.Title level={3} style={{ textAlign: "center" }}>
          实验室周报系统
        </Typography.Title>
        <Form onFinish={onFinish} layout="vertical" requiredMark={false}>
          <Form.Item name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input size="large" prefix={<UserOutlined />} placeholder="用户名" autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password size="large" prefix={<LockOutlined />} placeholder="密码" autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" size="large" block loading={loading}>
            登录
          </Button>
        </Form>
        <Typography.Paragraph type="secondary" style={{ marginTop: 16, fontSize: 12, textAlign: "center" }}>
          连续输错 3 次密码将锁定账号 10 分钟
        </Typography.Paragraph>
      </Card>
    </div>
  );
}

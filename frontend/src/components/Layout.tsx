import { Layout, Menu, Dropdown, Avatar, Typography } from "antd";
import {
  FileTextOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  UserOutlined,
  LogoutOutlined,
  KeyOutlined,
} from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const { Header, Content, Sider } = Layout;

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const items = [
    { key: "/", icon: <FileTextOutlined />, label: "周报" },
    ...(user?.role === "admin"
      ? [
          { key: "/admin/users", icon: <TeamOutlined />, label: "用户管理" },
          { key: "/admin/schedules", icon: <ClockCircleOutlined />, label: "定时任务" },
        ]
      : []),
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Typography.Title level={4} style={{ color: "#fff", margin: 0 }}>
          实验室周报系统
        </Typography.Title>
        <Dropdown
          menu={{
            items: [
              { key: "pwd", icon: <KeyOutlined />, label: "修改密码", onClick: () => navigate("/change-password") },
              { key: "out", icon: <LogoutOutlined />, label: "退出登录", onClick: () => logout().then(() => navigate("/login")) },
            ],
          }}
        >
          <span style={{ color: "#fff", cursor: "pointer" }}>
            <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: 8 }} />
            {user?.display_name}
            {user?.role === "admin" && "（管理员）"}
          </span>
        </Dropdown>
      </Header>
      <Layout>
        <Sider width={200} theme="light">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={items}
            onClick={(e) => navigate(e.key)}
            style={{ height: "100%", borderRight: 0 }}
          />
        </Sider>
        <Content style={{ padding: 24, background: "#f5f5f5" }}>
          <div style={{ background: "#fff", padding: 24, borderRadius: 12, minHeight: 360 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

import { useState } from "react";
import { Layout, Menu, Drawer, Dropdown, Avatar, Typography, Button, Grid } from "antd";
import {
  FileTextOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  UserOutlined,
  LogoutOutlined,
  KeyOutlined,
  MenuOutlined,
} from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import type { MenuProps } from "antd";
import { useAuth } from "../auth";

const { Header, Content, Sider } = Layout;
const { useBreakpoint } = Grid;

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();
  const isMobile = !screens.md; // < 768px
  const [drawerOpen, setDrawerOpen] = useState(false);

  const items = [
    { key: "/", icon: <FileTextOutlined />, label: "周报" },
    ...(user?.role === "admin"
      ? [
          { key: "/admin/users", icon: <TeamOutlined />, label: "用户管理" },
          { key: "/admin/schedules", icon: <ClockCircleOutlined />, label: "定时任务" },
        ]
      : []),
  ];
  const hasNav = items.length > 1; // normal users only have one page → no nav needed

  const onMenuClick: MenuProps["onClick"] = (e) => {
    navigate(e.key);
    setDrawerOpen(false);
  };

  const menu = (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname]}
      items={items}
      onClick={onMenuClick}
      style={{ height: "100%", borderRight: 0 }}
    />
  );

  const userMenuItems: MenuProps["items"] = [
    { key: "pwd", icon: <KeyOutlined />, label: "修改密码", onClick: () => navigate("/change-password") },
    { key: "out", icon: <LogoutOutlined />, label: "退出登录", onClick: () => logout().then(() => navigate("/login")) },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 20,
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: isMobile ? "0 12px" : "0 24px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          {isMobile && hasNav && (
            <Button
              type="text"
              icon={<MenuOutlined style={{ color: "#fff", fontSize: 18 }} />}
              onClick={() => setDrawerOpen(true)}
            />
          )}
          <Typography.Title
            level={isMobile ? 5 : 4}
            style={{ color: "#fff", margin: 0, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
          >
            {isMobile ? "周报系统" : "实验室周报系统"}
          </Typography.Title>
        </div>
        <Dropdown menu={{ items: userMenuItems }} trigger={["click"]}>
          <span style={{ color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", maxWidth: "55vw" }}>
            <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: 8, flex: "none" }} />
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.display_name}
              {user?.role === "admin" && !isMobile && "（管理员）"}
            </span>
          </span>
        </Dropdown>
      </Header>

      <Layout>
        {!isMobile && hasNav && (
          <Sider width={200} theme="light">
            {menu}
          </Sider>
        )}
        <Content style={{ padding: isMobile ? 12 : 24, background: "#f5f5f5" }}>
          <div
            style={{
              background: "#fff",
              padding: isMobile ? 16 : 24,
              borderRadius: 12,
              minHeight: 360,
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>

      <Drawer
        title="菜单"
        placement="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        styles={{ body: { padding: 0 } }}
        width={240}
      >
        {menu}
      </Drawer>
    </Layout>
  );
}

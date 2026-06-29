import { useEffect, useState } from "react";
import {
  Button,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { api, User } from "../api";

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [includeInactive, setIncludeInactive] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [pwdUser, setPwdUser] = useState<User | null>(null);
  const [createForm] = Form.useForm();
  const [pwdForm] = Form.useForm();

  const load = async () => {
    const { data } = await api.get<User[]>("/users", { params: { include_inactive: includeInactive } });
    setUsers(data);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeInactive]);

  const createUser = async () => {
    const values = await createForm.validateFields();
    try {
      await api.post("/users", values);
      message.success("用户已创建");
      setCreateOpen(false);
      createForm.resetFields();
      load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "创建失败");
    }
  };

  const patchUser = async (id: number, payload: Partial<User>) => {
    try {
      await api.patch(`/users/${id}`, payload);
      load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "操作失败");
    }
  };

  const resetPassword = async () => {
    if (!pwdUser) return;
    const { new_password } = await pwdForm.validateFields();
    await api.post(`/users/${pwdUser.id}/reset-password`, { new_password });
    message.success("密码已重置");
    setPwdUser(null);
    pwdForm.resetFields();
  };

  const deleteUser = async (id: number) => {
    try {
      await api.delete(`/users/${id}`);
      message.success("用户已删除");
      load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "删除失败");
    }
  };

  const columns = [
    { title: "姓名", dataIndex: "display_name" },
    { title: "用户名", dataIndex: "username" },
    {
      title: "角色",
      dataIndex: "role",
      render: (role: string, u: User) => (
        <Select
          size="small"
          value={role}
          style={{ width: 100 }}
          onChange={(v) => patchUser(u.id, { role: v as "admin" | "user" })}
          options={[
            { value: "user", label: "普通用户" },
            { value: "admin", label: "管理员" },
          ]}
        />
      ),
    },
    {
      title: "状态",
      dataIndex: "is_active",
      render: (active: boolean, u: User) => (
        <Space>
          <Switch checked={active} size="small" onChange={(v) => patchUser(u.id, { is_active: v })} />
          {active ? <Tag color="green">有效</Tag> : <Tag>已停用</Tag>}
        </Space>
      ),
    },
    {
      title: "操作",
      render: (_: unknown, u: User) => (
        <Space>
          <Button size="small" onClick={() => setPwdUser(u)}>
            重置密码
          </Button>
          <Popconfirm
            title="彻底删除该用户？"
            description="将连同其所有周报和图片一并删除，不可恢复。建议优先使用“停用”。"
            onConfirm={() => deleteUser(u.id)}
          >
            <Button size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16, width: "100%", justifyContent: "space-between" }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          用户管理
        </Typography.Title>
        <Space>
          <span>
            显示已停用用户 <Switch size="small" checked={includeInactive} onChange={setIncludeInactive} />
          </span>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新增用户
          </Button>
        </Space>
      </Space>

      <Table rowKey="id" columns={columns} dataSource={users} pagination={false} />

      <Modal title="新增用户" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={createUser} okText="创建" cancelText="取消">
        <Form form={createForm} layout="vertical" initialValues={{ role: "user" }}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }, { pattern: /^[A-Za-z0-9_.-]+$/, message: "仅限字母数字及 _.-" }]}>
            <Input placeholder="登录用用户名" />
          </Form.Item>
          <Form.Item name="display_name" label="姓名" rules={[{ required: true }]}>
            <Input placeholder="显示姓名" />
          </Form.Item>
          <Form.Item name="password" label="初始密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password placeholder="至少 6 位" />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Select
              options={[
                { value: "user", label: "普通用户" },
                { value: "admin", label: "管理员" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={`重置密码 - ${pwdUser?.display_name ?? ""}`} open={!!pwdUser} onCancel={() => setPwdUser(null)} onOk={resetPassword} okText="确定" cancelText="取消">
        <Form form={pwdForm} layout="vertical">
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password placeholder="至少 6 位" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

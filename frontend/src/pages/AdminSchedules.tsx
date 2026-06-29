import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Form,
  InputNumber,
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
import { api, Schedule } from "../api";

const WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
const MAX = 10;

export default function AdminSchedules() {
  const [items, setItems] = useState<Schedule[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Schedule | null>(null);
  const [form] = Form.useForm();

  const load = async () => {
    const { data } = await api.get<Schedule[]>("/schedules");
    setItems(data);
  };

  useEffect(() => {
    load();
  }, []);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ day_of_week: 0, hour: 9, minute: 0, enabled: true });
    setOpen(true);
  };

  const openEdit = (s: Schedule) => {
    setEditing(s);
    form.setFieldsValue(s);
    setOpen(true);
  };

  const submit = async () => {
    const values = await form.validateFields();
    try {
      if (editing) {
        await api.put(`/schedules/${editing.id}`, values);
      } else {
        await api.post("/schedules", values);
      }
      message.success("已保存");
      setOpen(false);
      load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "保存失败");
    }
  };

  const toggle = async (s: Schedule) => {
    await api.post(`/schedules/${s.id}/toggle`);
    load();
  };

  const remove = async (id: number) => {
    await api.delete(`/schedules/${id}`);
    message.success("已删除");
    load();
  };

  const columns = [
    { title: "名称", dataIndex: "name" },
    {
      title: "触发时间",
      render: (_: unknown, s: Schedule) =>
        `每${WEEKDAYS[s.day_of_week]} ${String(s.hour).padStart(2, "0")}:${String(s.minute).padStart(2, "0")}`,
    },
    {
      title: "开关",
      render: (_: unknown, s: Schedule) => (
        <Space>
          <Switch checked={s.enabled} onChange={() => toggle(s)} />
          {s.enabled ? <Tag color="green">启用</Tag> : <Tag>关闭</Tag>}
        </Space>
      ),
    },
    {
      title: "操作",
      render: (_: unknown, s: Schedule) => (
        <Space>
          <Button size="small" onClick={() => openEdit(s)}>
            编辑
          </Button>
          <Popconfirm title="删除该定时任务？" onConfirm={() => remove(s.id)}>
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
          定时任务（自动开启本周填报）
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} disabled={items.length >= MAX} onClick={openCreate}>
          新增定时任务
        </Button>
      </Space>

      <Alert
        style={{ marginBottom: 16 }}
        type="info"
        showIcon
        message={`最多可创建 ${MAX} 个定时任务（当前 ${items.length} 个）。时区：Asia/Shanghai。每个任务到点会自动“开启本周填报”，可像闹钟一样单独开关。`}
      />

      <Table rowKey="id" columns={columns} dataSource={items} pagination={false} />

      <Modal title={editing ? "编辑定时任务" : "新增定时任务"} open={open} onCancel={() => setOpen(false)} onOk={submit} okText="保存" cancelText="取消">
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input placeholder="例如：每周一组会前开启" />
          </Form.Item>
          <Form.Item name="day_of_week" label="星期" rules={[{ required: true }]}>
            <Select options={WEEKDAYS.map((w, i) => ({ value: i, label: w }))} />
          </Form.Item>
          <Space>
            <Form.Item name="hour" label="时" rules={[{ required: true }]}>
              <InputNumber min={0} max={23} />
            </Form.Item>
            <Form.Item name="minute" label="分" rules={[{ required: true }]}>
              <InputNumber min={0} max={59} />
            </Form.Item>
          </Space>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

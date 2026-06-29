import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Empty,
  Modal,
  Popconfirm,
  Select,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { EditOutlined, DeleteOutlined, PlayCircleOutlined, PauseCircleOutlined } from "@ant-design/icons";
import { api, Cycle, ReportWithUser } from "../api";
import { useAuth } from "../auth";
import RichTextEditor from "../components/RichTextEditor";
import RichTextViewer from "../components/RichTextViewer";

export default function Reports() {
  const { user } = useAuth();
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [currentLabel, setCurrentLabel] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [rows, setRows] = useState<ReportWithUser[]>([]);
  const [loading, setLoading] = useState(false);

  const [editing, setEditing] = useState(false);
  const [draftJson, setDraftJson] = useState("");
  const [draftHtml, setDraftHtml] = useState("");
  const [saving, setSaving] = useState(false);

  const selected = useMemo(() => cycles.find((c) => c.id === selectedId) || null, [cycles, selectedId]);
  const isCurrentWeek = selected?.week_label === currentLabel;
  // Own report editable: past weeks always; current week only when opened.
  const canEditOwn = selected ? (!isCurrentWeek || selected.is_open) : false;

  const loadCycles = async () => {
    const [cyclesRes, currentRes] = await Promise.all([
      api.get<Cycle[]>("/cycles"),
      api.get<Cycle | null>("/cycles/current"),
    ]);
    setCycles(cyclesRes.data);
    setCurrentLabel(currentRes.data?.week_label ?? null);
    setSelectedId((prev) => prev ?? currentRes.data?.id ?? cyclesRes.data[0]?.id ?? null);
  };

  const loadRows = async (cycleId: number) => {
    setLoading(true);
    try {
      const { data } = await api.get<ReportWithUser[]>(`/reports/by-cycle/${cycleId}`);
      setRows(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCycles();
  }, []);

  useEffect(() => {
    if (selectedId) loadRows(selectedId);
  }, [selectedId]);

  const openCurrentWeek = async () => {
    try {
      await api.post("/cycles/open-current");
      message.success("本周填报已开启");
      await loadCycles();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "操作失败");
    }
  };

  const closeWeek = async () => {
    if (!selected) return;
    await api.post(`/cycles/${selected.id}/close`);
    message.success("已关闭本周填报");
    loadCycles();
  };

  const myRow = rows.find((r) => r.user_id === user?.id);

  const startEdit = () => {
    setDraftJson(myRow?.report?.content_json || "");
    setDraftHtml(myRow?.report?.content_html || "");
    setEditing(true);
  };

  const saveDraft = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await api.put(`/reports/cycle/${selected.id}`, {
        content_html: draftHtml,
        content_json: draftJson,
      });
      message.success("已保存");
      setEditing(false);
      loadRows(selected.id);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const deleteReport = async (reportId: number) => {
    await api.delete(`/reports/${reportId}`);
    message.success("已删除");
    if (selected) loadRows(selected.id);
  };

  const currentWeekOpened = cycles.some((c) => c.week_label === currentLabel);

  return (
    <div>
      <Space style={{ marginBottom: 16, width: "100%", justifyContent: "space-between" }} wrap>
        <Space wrap>
          <Typography.Text strong>选择周次：</Typography.Text>
          <Select
            style={{ width: 280 }}
            value={selectedId ?? undefined}
            onChange={setSelectedId}
            placeholder="暂无周报周次"
            options={cycles.map((c) => ({
              value: c.id,
              label: `${c.week_label}（${c.start_date} ~ ${c.end_date}）${c.is_open ? "" : " · 已关闭"}`,
            }))}
          />
          {selected && (
            <Tag color={selected.is_open ? "green" : "default"}>{selected.is_open ? "填报中" : "已关闭"}</Tag>
          )}
          {isCurrentWeek && <Tag color="blue">本周</Tag>}
        </Space>
        {user?.role === "admin" && (
          <Space>
            {!currentWeekOpened ? (
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={openCurrentWeek}>
                开启本周填报
              </Button>
            ) : (
              isCurrentWeek &&
              selected?.is_open && (
                <Button icon={<PauseCircleOutlined />} onClick={closeWeek}>
                  关闭本周填报
                </Button>
              )
            )}
          </Space>
        )}
      </Space>

      {!currentWeekOpened && (
        <Alert
          style={{ marginBottom: 16 }}
          type="info"
          showIcon
          message="本周填报尚未开启"
          description={
            user?.role === "admin"
              ? "点击右上角“开启本周填报”后，成员即可填写本周周报；当前你仍可编辑自己的往期周报。"
              : "管理员尚未开启本周填报，你目前可以查看全部周报，或修改自己的往期周报。"
          }
        />
      )}

      {selected && canEditOwn && (
        <Card style={{ marginBottom: 16, background: "#f9f9ff", borderColor: "#c7d2fe" }}>
          <Space style={{ width: "100%", justifyContent: "space-between" }}>
            <span>
              <Typography.Text strong>我的周报</Typography.Text>
              {myRow?.report && (
                <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                  最近更新：{new Date(myRow.report.updated_at).toLocaleString()}
                </Typography.Text>
              )}
            </span>
            <Button type="primary" icon={<EditOutlined />} onClick={startEdit}>
              {myRow?.report ? "编辑我的周报" : "填写本周周报"}
            </Button>
          </Space>
        </Card>
      )}

      {rows.length === 0 && !loading ? (
        <Empty description="暂无数据" />
      ) : (
        <Space direction="vertical" style={{ width: "100%" }} size={16}>
          {rows.map((r) => (
            <Card
              key={r.user_id}
              size="small"
              title={
                <Space>
                  <Typography.Text strong>{r.display_name}</Typography.Text>
                  <Typography.Text type="secondary">@{r.username}</Typography.Text>
                  {r.user_id === user?.id && <Tag color="blue">我</Tag>}
                </Space>
              }
              extra={
                user?.role === "admin" && r.report ? (
                  <Popconfirm title="删除该周报？图片也会一并删除" onConfirm={() => deleteReport(r.report!.id)}>
                    <Button danger size="small" icon={<DeleteOutlined />}>
                      删除
                    </Button>
                  </Popconfirm>
                ) : null
              }
            >
              <RichTextViewer html={r.report?.content_html || ""} />
            </Card>
          ))}
        </Space>
      )}

      <Modal
        title="编辑周报"
        open={editing}
        onCancel={() => setEditing(false)}
        onOk={saveDraft}
        confirmLoading={saving}
        okText="保存"
        cancelText="取消"
        width={820}
        destroyOnClose
      >
        <RichTextEditor
          initialContent={draftJson}
          onChange={(json, html) => {
            setDraftJson(json);
            setDraftHtml(html);
          }}
        />
      </Modal>
    </div>
  );
}

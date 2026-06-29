# 实验室周报系统 (Weekly Report)

面向计算机方向实验室（约 20 人）的内部周报系统：长期保存每周周报（文字 + 图片），
两类角色（管理员 / 普通用户），自带认证与防暴力破解，单 Podman 容器交付，
通过 nginx 反代到 `mydomain.com/weekly_report`。

## 功能

- **普通用户**：查看所有有效用户的本周 / 往期周报；用富文本（文字 + 图片）填写、修改**自己**的周报；本周需管理员开启填报后才能写本周，往期周报随时可改。
- **管理员**：新增 / 停用 / 删除用户、重置密码；删除往期周报释放空间；一键“开启本周填报”；管理最多 10 个定时任务（自动开启本周填报，可单独开关，类似闹钟）。
- **安全**：argon2 密码哈希；httpOnly + SameSite 会话 Cookie + CSRF 双提交校验；同一账号连续输错 3 次锁定 10 分钟；富文本前后端双重净化防 XSS；图片上传校验类型/大小，访问需登录。

## 技术栈

- 后端：FastAPI + SQLAlchemy（SQLite）+ APScheduler，Python 3.12
- 前端：React + Vite + TypeScript + Ant Design + TipTap 富文本
- 部署：单容器（FastAPI 同时提供 API 与 React 静态资源，SQLite 内嵌），数据落在挂载卷 `/data`

## 部署

1. 准备配置：
   ```bash
   cp .env.example .env
   # 编辑 .env：设置 SECRET_KEY（openssl rand -hex 32）、ADMIN_USERNAME、ADMIN_PASSWORD
   ```
2. 构建并启动：
   ```bash
   ./run.sh
   ```
   容器监听 `127.0.0.1:8080`，仅本机 nginx 可访问。
3. nginx：把 `nginx.snippet` 的内容粘贴进现有 `server { }`，`nginx -t && systemctl reload nginx`。
4. 访问 `https://mydomain.com/weekly_report/`，用 `.env` 里的管理员账号登录，**首次登录后请立即修改密码**。
5. （可选）开机自启：见 `weekly-report.container`（systemd Quadlet）。

## 数据与备份

- 所有数据（`app.db` + `uploads/`）都在 Podman 卷 `weekly_data`（容器内 `/data`）。
- 备份：`./backup.sh [输出目录]` → 生成带时间戳的 `.tar.gz`。
- 恢复：`./restore.sh path/to/backup.tar.gz`。

## 本地开发

后端：
```bash
cd backend
pip install -r requirements.txt
DATA_DIR=./data COOKIE_SECURE=false uvicorn app.main:app --reload --port 8080
```
前端（另开终端）：
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173/weekly_report/ ，API 自动代理到 :8080
```

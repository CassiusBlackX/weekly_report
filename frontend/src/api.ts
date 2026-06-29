import axios from "axios";

export const BASE_PATH = "/weekly_report";

export const api = axios.create({
  baseURL: `${BASE_PATH}/api`,
  withCredentials: true,
});

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : null;
}

// Attach the double-submit CSRF token to every state-changing request.
api.interceptors.request.use((config) => {
  const method = (config.method || "get").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = readCookie("wr_csrf");
    if (token) {
      config.headers = config.headers ?? {};
      config.headers["X-CSRF-Token"] = token;
    }
  }
  return config;
});

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
}

export interface Cycle {
  id: number;
  week_label: string;
  start_date: string;
  end_date: string;
  is_open: boolean;
  opened_at: string;
}

export interface Report {
  id: number;
  cycle_id: number;
  user_id: number;
  content_html: string;
  content_json: string;
  updated_at: string;
}

export interface ReportWithUser {
  user_id: number;
  username: string;
  display_name: string;
  report: Report | null;
}

export interface Schedule {
  id: number;
  name: string;
  day_of_week: number;
  hour: number;
  minute: number;
  enabled: boolean;
  created_at: string;
}

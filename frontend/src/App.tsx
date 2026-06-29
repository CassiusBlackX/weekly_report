import { Navigate, Route, Routes } from "react-router-dom";
import { Spin } from "antd";
import { useAuth } from "./auth";
import AppLayout from "./components/Layout";
import Login from "./pages/Login";
import Reports from "./pages/Reports";
import AdminUsers from "./pages/AdminUsers";
import AdminSchedules from "./pages/AdminSchedules";
import ChangePassword from "./pages/ChangePassword";

function Protected({ children, adminOnly }: { children: JSX.Element; adminOnly?: boolean }) {
  const { user, loading } = useAuth();
  if (loading) return <Spin style={{ display: "block", marginTop: 120 }} size="large" />;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route index element={<Reports />} />
        <Route path="change-password" element={<ChangePassword />} />
        <Route
          path="admin/users"
          element={
            <Protected adminOnly>
              <AdminUsers />
            </Protected>
          }
        />
        <Route
          path="admin/schedules"
          element={
            <Protected adminOnly>
              <AdminSchedules />
            </Protected>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

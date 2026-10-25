import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/login";
import Register from "./pages/register";
import Dashboard from "./pages/dashboard";

function Protected({ children }) {
  return localStorage.getItem("token") ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}
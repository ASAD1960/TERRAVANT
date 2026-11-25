import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { Spinner } from "./components/common/ui";
import AppLayout from "./layouts/AppLayout";
import Landing from "./pages/Landing";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";
import { RequireAuth } from "./routes/Guards";

const Dashboard = lazy(() => import("./pages/farmer/Dashboard"));
const Farms = lazy(() => import("./pages/farmer/Farms"));
const FarmDetail = lazy(() => import("./pages/farmer/FarmDetail"));
const Crop = lazy(() => import("./pages/farmer/CropRecommendation"));
const Disease = lazy(() => import("./pages/farmer/DiseaseDetection"));
const Yield = lazy(() => import("./pages/farmer/YieldPrediction"));
const Fertilizer = lazy(() => import("./pages/farmer/Fertilizer"));
const Weather = lazy(() => import("./pages/farmer/Weather"));
const Notifications = lazy(() => import("./pages/farmer/Notifications"));
const Admin = lazy(() => import("./pages/admin/Admin"));

export default function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route element={<RequireAuth />}>
          <Route path="/app" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="farms" element={<Farms />} />
            <Route path="farms/:id" element={<FarmDetail />} />
            <Route path="crops" element={<Crop />} />
            <Route path="disease" element={<Disease />} />
            <Route path="yield" element={<Yield />} />
            <Route path="fertilizer" element={<Fertilizer />} />
            <Route path="weather" element={<Weather />} />
            <Route path="notifications" element={<Notifications />} />
            <Route element={<RequireAuth roles={["admin", "operator"]} />}><Route path="admin" element={<Admin />} /></Route>
          </Route>
        </Route>
        <Route path="*" element={<div className="p-10 text-center"><p className="text-xl font-bold">Page not found</p><a className="text-forest underline" href="/">Go home</a></div>} />
      </Routes>
    </Suspense>
  );
}

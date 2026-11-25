import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import type { z } from "zod";
import { Banner, TextField } from "../../components/common/ui";
import { useAuth } from "../../hooks/useAuth";
import { loginSchema } from "../../utils/schemas";
import AuthShell from "./AuthShell";

type Form = z.infer<typeof loginSchema>;

export default function Login() {
  const { login, user } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({ resolver: zodResolver(loginSchema) });
  if (user) return <Navigate to="/app" replace />;

  const onSubmit = async (v: Form) => {
    setError(null);
    try { await login(v.email, v.password); nav((loc.state as { from?: string } | null)?.from ?? "/app", { replace: true }); }
    catch (e) { setError((e as Error).message); }
  };
  return (
    <AuthShell title="Sign in" subtitle="Use the email and password for your TERRAVANT account."
      footer={<>New to TERRAVANT? <Link className="font-semibold text-forest underline" to="/register">Create an account</Link></>}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        {error && <Banner kind="error">{error}</Banner>}
        <TextField label="Email" type="email" autoComplete="email" {...register("email")} error={errors.email?.message} />
        <div className="space-y-2">
          <TextField label="Password" type="password" autoComplete="current-password" {...register("password")} error={errors.password?.message} />
          <div className="text-right"><Link className="text-sm font-semibold text-forest underline" to="/forgot-password">Forgot password?</Link></div>
        </div>
        <button type="submit" className="btn w-full" disabled={isSubmitting}>{isSubmitting ? "Signing in…" : "Sign in"}</button>
      </form>
    </AuthShell>
  );
}

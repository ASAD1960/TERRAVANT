
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import type { z } from "zod";
import { Banner, SelectField, TextField } from "../../components/common/ui";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import { registerSchema } from "../../utils/schemas";
import AuthShell from "./AuthShell";

type Form = z.infer<typeof registerSchema>;

export default function Register() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<Form>({
    resolver: zodResolver(registerSchema),
    defaultValues: { account_type: "farmer" },
  });

  const isBusiness = watch("account_type") === "business";

  const onSubmit = async (values: Form) => {
    setError(null);

    try {
      await api("/auth/register", {
        json: {
          ...values,
          phone: values.phone || null,
          organization: values.organization || null,
        },
      });

      await login(values.email, values.password);
      nav("/app", { replace: true });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start with a clearer view of your agricultural operations."
      footer={
        <>
          Already registered?{" "}
          <Link className="font-semibold text-forest underline" to="/login">
            Sign in
          </Link>
        </>
      }
    >
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="tv-register-form space-y-4"
        noValidate
      >
        {error && <Banner kind="error">{error}</Banner>}

        <div className="tv-register-section">
          <div className="tv-register-section-heading">
            <span className="tv-register-step">01</span>
            <span>Account information</span>
          </div>

          <div className="space-y-4">
            <SelectField
              label="Account type"
              {...register("account_type")}
              options={[
                { value: "farmer", label: "Farmer" },
                { value: "business", label: "Agricultural business" },
              ]}
            />

            <TextField
              label="Full name"
              autoComplete="name"
              {...register("full_name")}
              error={errors.full_name?.message}
            />

            {isBusiness && (
              <TextField
                label="Business name"
                autoComplete="organization"
                {...register("organization")}
                error={errors.organization?.message}
              />
            )}
          </div>
        </div>

        <div className="tv-register-section">
          <div className="tv-register-section-heading">
            <span className="tv-register-step">02</span>
            <span>Contact details</span>
          </div>

          <div className="space-y-4">
            <TextField
              label="Email address"
              type="email"
              autoComplete="email"
              {...register("email")}
              error={errors.email?.message}
            />

            <TextField
              label="Phone number"
              type="tel"
              autoComplete="tel"
              {...register("phone")}
              error={errors.phone?.message}
              hint="Optional"
            />
          </div>
        </div>

        <div className="tv-register-section">
          <div className="tv-register-section-heading">
            <span className="tv-register-step">03</span>
            <span>Secure your account</span>
          </div>

          <TextField
            label="Password"
            type="password"
            autoComplete="new-password"
            hint="At least 10 characters, including letters and numbers."
            {...register("password")}
            error={errors.password?.message}
          />
        </div>

        <button
          className="btn tv-register-submit w-full"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Creating account…" : "Create your account"}
        </button>

        <p className="tv-register-note">
          Your account is protected with secure authentication.
        </p>
      </form>
    </AuthShell>
  );
}


import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router-dom";
import type { z } from "zod";
import { Banner, TextField } from "../../components/common/ui";
import { api } from "../../services/api";
import { resetPasswordSchema } from "../../utils/schemas";
import AuthShell from "./AuthShell";

type Form = z.infer<typeof resetPasswordSchema>;

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token")?.trim() ?? "";

  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Form>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (values: Form) => {
    setError(null);

    try {
      await api("/auth/reset-password", {
        json: {
          token,
          new_password: values.new_password,
        },
      });

      setSuccess(true);
    } catch (e) {
      setError(
        (e as Error).message || "The reset link is invalid or expired.",
      );
    }
  };

  return (
    <AuthShell
      title={
        success
          ? "Password updated"
          : "Choose a new password"
      }
      subtitle={
        success
          ? "Your account security credentials have been updated."
          : "Create a strong password to secure your TERRAVANT account."
      }
      footer={
        <Link className="font-semibold text-forest underline" to="/login">
          Back to sign in
        </Link>
      }
    >
      <div className="tv-recovery-form space-y-5">
        {success ? (
          <div className="tv-recovery-success space-y-4">
            <div className="tv-recovery-icon" aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M20 6 9 17l-5-5" />
                <circle cx="12" cy="12" r="10" />
              </svg>
            </div>

            <div>
              <h3 className="font-semibold text-forest">
                You're all set
              </h3>
              <p className="mt-2 text-sm leading-6 text-charcoal/70">
                Your password has been updated successfully. You can now
                sign in using your new password.
              </p>
            </div>

            <Link
              to="/login"
              className="btn tv-recovery-submit flex w-full items-center justify-center"
            >
              Continue to sign in
            </Link>
          </div>
        ) : !token ? (
          <div className="space-y-4">
            <Banner kind="error">
              This reset link is missing its token. Request a new password
              reset link.
            </Banner>

            <Link
              to="/forgot-password"
              className="btn tv-recovery-submit flex w-full items-center justify-center"
            >
              Request a new link
            </Link>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-5"
            noValidate
          >
            {error && <Banner kind="error">{error}</Banner>}

            <div className="space-y-4">
              <TextField
                label="New password"
                type="password"
                autoComplete="new-password"
                hint="At least 10 characters, including letters and numbers."
                {...register("new_password")}
                error={errors.new_password?.message}
              />

              <TextField
                label="Confirm new password"
                type="password"
                autoComplete="new-password"
                {...register("confirm_password")}
                error={errors.confirm_password?.message}
              />
            </div>

            <button
              className="btn tv-recovery-submit w-full"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Updating password…" : "Update password"}
            </button>
          </form>
        )}
      </div>
    </AuthShell>
  );
}

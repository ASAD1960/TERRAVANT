
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import type { z } from "zod";
import { Banner, TextField } from "../../components/common/ui";
import { api } from "../../services/api";
import { forgotPasswordSchema } from "../../utils/schemas";
import AuthShell from "./AuthShell";

type Form = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Form>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (values: Form) => {
    setError(null);

    try {
      await api("/auth/forgot-password", {
        json: { email: values.email },
      });
      setSent(true);
    } catch {
      setError("We could not process your request. Please try again.");
    }
  };

  return (
    <AuthShell
      title={sent ? "Check your inbox" : "Reset your password"}
      subtitle={
        sent
          ? "Your next step is in your email."
          : "Recover access to your TERRAVANT account securely."
      }
      footer={
        <Link className="font-semibold text-forest underline" to="/login">
          Back to sign in
        </Link>
      }
    >
      <div className="tv-recovery-form space-y-5">
        {sent ? (
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
                <rect x="3" y="5" width="18" height="14" rx="2" />
                <path d="m3 7 9 6 9-6" />
                <path d="m8 17 2 2 5-5" />
              </svg>
            </div>

            <div>
              <h3 className="font-semibold text-forest">
                Request received
              </h3>
              <p className="mt-2 text-sm leading-6 text-charcoal/70">
                If an account exists for that email, a password reset link
                has been sent. Please check your inbox and spam folder.
              </p>
            </div>

            <Banner>
              For security, we do not reveal whether an email address has an
              account.
            </Banner>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-5"
            noValidate
          >
            {error && <Banner kind="error">{error}</Banner>}

            <TextField
              label="Email address"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              {...register("email")}
              error={errors.email?.message}
            />

            <button
              className="btn tv-recovery-submit w-full"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Sending reset link…" : "Send reset link"}
            </button>

            <p className="text-center text-xs leading-5 text-charcoal/55">
              If your account exists, we will send instructions to your
              registered email address.
            </p>
          </form>
        )}
      </div>
    </AuthShell>
  );
}

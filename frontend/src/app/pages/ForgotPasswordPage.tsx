import { useState } from "react";
import { motion } from "motion/react";
import { useNavigate } from "react-router";
import { ArrowRight, Hand } from "lucide-react";

import { forgotPassword } from "../api/auth";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setError("Enter a valid email address");
      return;
    }

    try {
      setLoading(true);

      const response = await forgotPassword(email);

      setMessage(response.message);
    } catch (error: any) {
      setError(
        error.response?.data?.detail ||
          "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="flex-1 flex items-start justify-center px-4 py-12"
      style={{ fontFamily: "Inter, sans-serif" }}
    >
      <div className="w-full max-w-xl">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.3,
            ease: "easeOut",
          }}
        >
          <div className="text-center mb-8">
            <div
              className="mx-auto mb-4 flex items-center justify-center rounded-2xl"
              style={{
                width: 52,
                height: 52,
                background: "#6C47FF",
              }}
            >
              <Hand size={24} color="white" />
            </div>

            <h1
              className="font-black text-4xl mb-2"
              style={{
                color: "#1A1535",
                fontFamily: "Nunito, sans-serif",
              }}
            >
              Forgot your password?
            </h1>

            <p
              className="text-sm"
              style={{ color: "#7B7BA0" }}
            >
              Enter your email and we'll send you a
              password reset link.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-3xl p-8 shadow-sm flex flex-col gap-5"
            style={{
              background: "#FFFFFF",
              border: "1px solid #E2E0F8",
            }}
          >
            <div className="flex flex-col gap-1.5">
              <label
                className="text-sm font-semibold"
                style={{ color: "#1A1535" }}
              >
                Email address
              </label>

              <input
                type="email"
                placeholder="alex@example.com"
                value={email}
                onChange={(e) =>
                  setEmail(e.target.value)
                }
                className="w-full px-4 py-3.5 rounded-2xl text-sm outline-none"
                style={{
                  background: "#F5F4FF",
                  border: `2px solid ${
                    error ? "#EF4444" : "#E2E0F8"
                  }`,
                  color: "#1A1535",
                }}
              />

              {error && (
                <p
                  className="text-xs font-medium"
                  style={{ color: "#EF4444" }}
                >
                  {error}
                </p>
              )}
            </div>

            {message && (
              <p
                className="text-sm text-center font-medium"
                style={{ color: "#16A34A" }}
              >
                {message}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold text-base"
              style={{
                background:
                  "linear-gradient(135deg, #6C47FF 0%, #9D7BFF 100%)",
                color: "white",
                fontFamily: "Nunito, sans-serif",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading
                ? "Sending..."
                : "Send reset link"}

              <ArrowRight size={18} />
            </button>

            <p
              className="text-sm text-center"
              style={{ color: "#7B7BA0" }}
            >
              Remember your password?{" "}

              <button
                type="button"
                className="font-semibold"
                style={{ color: "#6C47FF" }}
                onClick={() => navigate("/signin")}
              >
                Sign in
              </button>
            </p>
          </form>
        </motion.div>
      </div>
    </div>
  );
}

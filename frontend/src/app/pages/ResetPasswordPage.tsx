import { useState } from "react";
import { motion } from "motion/react";
import {
  useNavigate,
  useSearchParams,
} from "react-router";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Hand,
} from "lucide-react";

import { resetPassword } from "../api/auth";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!token) {
      setError(
        "Invalid or missing password reset link."
      );
      return;
    }

    if (password.length < 8) {
      setError(
        "Password must be at least 8 characters."
      );
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);

      const response = await resetPassword(
        token,
        password
      );

      setMessage(response.message);

      setTimeout(() => {
        navigate("/signin");
      }, 1500);
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
              Reset password
            </h1>

            <p
              className="text-sm"
              style={{ color: "#7B7BA0" }}
            >
              Choose a new password for your account.
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
            {/* New password */}
            <div className="flex flex-col gap-1.5">
              <label
                className="text-sm font-semibold"
                style={{ color: "#1A1535" }}
              >
                New password
              </label>

              <div className="relative">
                <input
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  placeholder="Enter new password"
                  value={password}
                  onChange={(e) =>
                    setPassword(e.target.value)
                  }
                  className="w-full px-4 py-3.5 rounded-2xl text-sm outline-none"
                  style={{
                    background: "#F5F4FF",
                    border: "2px solid #E2E0F8",
                    color: "#1A1535",
                    paddingRight: 44,
                  }}
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(
                      (value) => !value
                    )
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                  style={{ color: "#C4B0FF" }}
                >
                  {showPassword ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}
                </button>
              </div>
            </div>

            {/* Confirm password */}
            <div className="flex flex-col gap-1.5">
              <label
                className="text-sm font-semibold"
                style={{ color: "#1A1535" }}
              >
                Confirm password
              </label>

              <div className="relative">
                <input
                  type={
                    showConfirmPassword
                      ? "text"
                      : "password"
                  }
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) =>
                    setConfirmPassword(
                      e.target.value
                    )
                  }
                  className="w-full px-4 py-3.5 rounded-2xl text-sm outline-none"
                  style={{
                    background: "#F5F4FF",
                    border: "2px solid #E2E0F8",
                    color: "#1A1535",
                    paddingRight: 44,
                  }}
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowConfirmPassword(
                      (value) => !value
                    )
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                  style={{ color: "#C4B0FF" }}
                >
                  {showConfirmPassword ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <p
                className="text-sm text-center font-medium"
                style={{ color: "#EF4444" }}
              >
                {error}
              </p>
            )}

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
                ? "Resetting..."
                : "Reset password"}

              <ArrowRight size={18} />
            </button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}

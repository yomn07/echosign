import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useNavigate } from "react-router";
import { Eye, EyeOff, Check, ArrowRight, Hand } from "lucide-react";
import { signinUser } from "../api/auth";

function InputField({
  label, type = "text", placeholder, value, onChange, error,
  showToggle, onToggle,
}: {
  label: string; type?: string; placeholder: string; value: string;
  onChange: (v: string) => void; error?: string;
  showToggle?: boolean; onToggle?: () => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-semibold" style={{ color: "#1A1535" }}>{label}</label>
      <div className="relative">
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full px-4 py-3.5 rounded-2xl text-sm outline-none transition-all"
          style={{
            background: "#F5F4FF",
            border: `2px solid ${error ? "#EF4444" : "#E2E0F8"}`,
            color: "#1A1535",
            fontFamily: "Inter, sans-serif",
            paddingRight: showToggle ? 44 : 16,
          }}
          onFocus={e => { if (!error) e.target.style.borderColor = "#6C47FF"; }}
          onBlur={e => { if (!error) e.target.style.borderColor = "#E2E0F8"; }}
        />
        {showToggle && (
          <button type="button" onClick={onToggle}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg"
            style={{ color: "#C4B0FF" }}>
            {type === "password" ? <Eye size={16} /> : <EyeOff size={16} />}
          </button>
        )}
      </div>
      {error && <p className="text-xs font-medium" style={{ color: "#EF4444" }}>{error}</p>}
    </div>
  );
}

type FormData = { email: string; password: string };
type FormErrors = Partial<Record<keyof FormData, string>>;

export default function SignInPage() {
  const navigate = useNavigate();
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState("");

  const [form, setForm] = useState<FormData>({ email: "", password: "" });
  const [errors, setErrors] = useState<FormErrors>({});

  const set = (field: keyof FormData) => (v: string) =>
    setForm(f => ({ ...f, [field]: v }));

  const validate = (): boolean => {
    const e: FormErrors = {};
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = "Enter a valid email address";
    if (!form.password) e.password = "Password is required";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
    setLoading(true);
    setServerError("");

    const response = await signinUser({
        email: form.email,
        password: form.password,
    });


    sessionStorage.setItem(
        "access_token",
        response.access_token
    );


    sessionStorage.setItem(
        "user",
        JSON.stringify(response.user)
    );


    navigate("/");


    } catch (error: any) {

    if (error.response?.data?.detail) {
        setServerError(error.response.data.detail);
    } else {
        setServerError("Something went wrong. Please try again.");
    }

    } finally {
    setLoading(false);
    }}

  
  
  return (
    <div className="flex-1 flex items-start justify-center px-4 py-12" style={{ fontFamily: "Inter, sans-serif" }}>
      <div className="w-full max-w-xl">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}>

          {/* Header */}
          <div className="text-center mb-8">
            <div className="mx-auto mb-4 flex items-center justify-center rounded-2xl"
              style={{ width: 52, height: 52, background: "#6C47FF" }}>
              <Hand size={24} color="white" />
            </div>
            <h1 className="font-black text-4xl mb-2" style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif", letterSpacing: "-0.02em" }}>
              Welcome back
            </h1>
            <p className="text-sm" style={{ color: "#7B7BA0" }}>
              Sign in to continue learning and translating.
            </p>
          </div>

          <form onSubmit={handleSubmit}
            className="rounded-3xl p-8 shadow-sm flex flex-col gap-5"
            style={{ background: "#FFFFFF", border: "1px solid #E2E0F8" }}>

            <InputField label="Email address" type="email" placeholder="alex@example.com"
              value={form.email} onChange={set("email")} error={errors.email} />

            <InputField label="Password" type={showPass ? "text" : "password"}
              placeholder="Enter your password" value={form.password}
              onChange={set("password")} error={errors.password}
              showToggle onToggle={() => setShowPass(s => !s)} />

            <p
              className="text-sm text-right -mt-2"
              style={{ color: "#6C47FF" }}
            >
              <button
                type="button"
                className="font-semibold cursor-pointer"
                onClick={() => navigate("/forgot-password")}
              >
                Forgot password?
              </button>
            </p>

            {serverError && (
              <p className="text-sm text-center font-medium" style={{ color: "#EF4444" }}>
                {serverError}
              </p>
            )}

            <button type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold text-base transition-all hover:scale-[1.02] hover:shadow-lg mt-1"
              style={{
                background: "linear-gradient(135deg, #6C47FF 0%, #9D7BFF 100%)",
                color: "white",
                fontFamily: "Nunito, sans-serif",
                opacity: loading ? 0.7 : 1,
              }}>
              {loading ? "Signing in..." : "Sign in"} <ArrowRight size={18} />
            </button>

            <p className="text-sm text-center" style={{ color: "#7B7BA0" }}>
              Don't have an account?{" "}
              <span className="font-semibold cursor-pointer" style={{ color: "#6C47FF" }}
                onClick={() => navigate("/signup")}>
                Create one
              </span>
            </p>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
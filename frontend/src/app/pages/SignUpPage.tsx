import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useNavigate } from "react-router";
import { Eye, EyeOff, Check, ArrowRight, Hand } from "lucide-react";
import { registerUser } from "../api/auth";

function InputField({
  label, type = "text", placeholder, value, onChange, error, hint,
  showToggle, onToggle,
}: {
  label: string; type?: string; placeholder: string; value: string;
  onChange: (v: string) => void; error?: string; hint?: string;
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
      {hint && !error && <p className="text-xs" style={{ color: "#7B7BA0" }}>{hint}</p>}
    </div>
  );
}

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: "At least 8 characters", pass: password.length >= 8 },
    { label: "Contains a number", pass: /\d/.test(password) },
    { label: "Contains uppercase", pass: /[A-Z]/.test(password) },
    { label: "Contains a symbol", pass: /[!@#$%^&*]/.test(password) },
  ];
  const score = checks.filter(c => c.pass).length;
  const colors = ["#EF4444", "#F59E0B", "#10B981", "#10B981"];
  const labels = ["Weak", "Fair", "Strong", "Very strong"];

  if (!password) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="flex-1 rounded-full transition-all" style={{ height: 4, background: i < score ? colors[score - 1] : "#E2E0F8" }} />
        ))}
      </div>
      <div className="text-xs font-medium" style={{ color: score > 0 ? colors[score - 1] : "#7B7BA0" }}>
        {score > 0 ? labels[score - 1] : ""}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {checks.map(({ label, pass }) => (
          <div key={label} className="flex items-center gap-1 text-xs" style={{ color: pass ? "#10B981" : "#C4B0FF" }}>
            <Check size={11} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

type FormData = {
  firstName: string; lastName: string;
  email: string; password: string; confirm: string;
  role: string; agree: boolean;
};

type FormErrors = Partial<Record<keyof FormData, string>>;

export default function SignUpPage() {
  const navigate = useNavigate();
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [done, setDone] = useState(false);

  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState("");

  const [form, setForm] = useState<FormData>({
    firstName: "", lastName: "", email: "", password: "", confirm: "", role: "", agree: false,
  });
  const [errors, setErrors] = useState<FormErrors>({});

  const set = (field: keyof FormData) => (v: string | boolean) =>
    setForm(f => ({ ...f, [field]: v }));

  const validate = (): boolean => {
    const e: FormErrors = {};
    if (!form.firstName.trim()) e.firstName = "First name is required";
    if (!form.lastName.trim()) e.lastName = "Last name is required";
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = "Enter a valid email address";
    if (form.password.length < 8) e.password = "Password must be at least 8 characters";
    if (form.password !== form.confirm) e.confirm = "Passwords do not match";
    if (!form.agree) e.agree = "You must accept the terms to continue";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!validate()) return;

  try {
    setLoading(true);
    setServerError("");

    const response = await registerUser({
      first_name: form.firstName,
      last_name: form.lastName,
      email: form.email,
      password: form.password,
      role: form.role || undefined,
    });

    console.log(response);

    setDone(true);

  } catch (error: any) {

    if (error.response?.data?.detail) {

      setServerError(
        error.response.data.detail
      );

    } else {

      setServerError(
        "Something went wrong. Please try again."
      );
    }

  } finally {

    setLoading(false);
  }
};

  const roles = ["I am Deaf or hard of hearing", "I am learning sign language", "Educator or therapist", "Developer / researcher", "Other"];

  return (
    <div className="flex-1 flex items-start justify-center px-4 py-12" style={{ fontFamily: "Inter, sans-serif" }}>
      <div className="w-full max-w-xl">

        <AnimatePresence mode="wait">
                {done ? (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="rounded-3xl p-12 text-center shadow-sm"
                    style={{
                      background: "#FFFFFF",
                      border: "1px solid #E2E0F8"
                    }}
                  >

                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{
                        delay: 0.15,
                        type: "spring",
                        stiffness: 220
                      }}
                      className="mx-auto mb-6 flex items-center justify-center rounded-full"
                      style={{
                        width: 80,
                        height: 80,
                        background:
                          "linear-gradient(135deg, #6C47FF, #9D7BFF)"
                      }}
                    >
                      <Check
                        size={36}
                        color="white"
                        strokeWidth={3}
                      />
                    </motion.div>

                    <h2
                      className="font-black text-3xl mb-3"
                      style={{
                        color: "#1A1535",
                        fontFamily: "Nunito, sans-serif"
                      }}
                    >
                      Check your email!
                    </h2>

                    <p
                      className="text-base mb-3 leading-relaxed"
                      style={{ color: "#7B7BA0" }}
                    >
                      We've sent a verification link to:
                    </p>

                    <p
                      className="font-bold mb-6"
                      style={{ color: "#6C47FF" }}
                    >
                      {form.email}
                    </p>

                    <p
                      className="text-sm mb-8 leading-relaxed"
                      style={{ color: "#7B7BA0" }}
                    >
                      Click the link in the email to verify your
                      account. The link will expire in 30 minutes.
                    </p>

                    <button
                      onClick={() => navigate("/signin")}
                      className="flex items-center justify-center gap-2
                                px-7 py-3.5 rounded-2xl
                                font-semibold text-sm
                                transition-all hover:scale-105
                                mx-auto"
                      style={{
                        background: "#6C47FF",
                        color: "white"
                      }}
                    >
                      Go to sign in
                      <ArrowRight size={16} />
                    </button>

                  </motion.div>
                ) : (
            /* ── Form ───────────────────────────────────────────────────── */
            <motion.div key="form" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}>

              {/* Header */}
              <div className="text-center mb-8">
                <div className="mx-auto mb-4 flex items-center justify-center rounded-2xl"
                  style={{ width: 52, height: 52, background: "#6C47FF" }}>
                  <Hand size={24} color="white" />
                </div>
                <h1 className="font-black text-4xl mb-2" style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif", letterSpacing: "-0.02em" }}>
                  Create your account
                </h1>
                <p className="text-sm" style={{ color: "#7B7BA0" }}>
                  Free forever. No credit card needed.
                </p>
              </div>

              {/* Perks */}
              <div className="flex flex-wrap justify-center gap-3 mb-8">
                {["Save your history", "Personal word list", "Progress tracking", "Early access to new signs"].map(p => (
                  <div key={p} className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full"
                    style={{ background: "#EEF0FF", color: "#6C47FF" }}>
                    <Check size={11} /> {p}
                  </div>
                ))}
              </div>

              <form onSubmit={handleSubmit}
                className="rounded-3xl p-8 shadow-sm flex flex-col gap-5"
                style={{ background: "#FFFFFF", border: "1px solid #E2E0F8" }}>

                {/* Name row */}
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="First name" placeholder="Alex" value={form.firstName}
                    onChange={set("firstName")} error={errors.firstName} />
                  <InputField label="Last name" placeholder="Johnson" value={form.lastName}
                    onChange={set("lastName")} error={errors.lastName} />
                </div>

                <InputField label="Email address" type="email" placeholder="alex@example.com"
                  value={form.email} onChange={set("email")} error={errors.email} />

                <div>
                  <InputField label="Password" type={showPass ? "text" : "password"}
                    placeholder="Create a strong password" value={form.password}
                    onChange={set("password")} error={errors.password}
                    showToggle onToggle={() => setShowPass(s => !s)} />
                  {form.password && (
                    <div className="mt-3">
                      <PasswordStrength password={form.password} />
                    </div>
                  )}
                </div>

                <InputField label="Confirm password" type={showConfirm ? "text" : "password"}
                  placeholder="Repeat your password" value={form.confirm}
                  onChange={set("confirm")} error={errors.confirm}
                  showToggle onToggle={() => setShowConfirm(s => !s)} />

                {/* Role select */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-semibold" style={{ color: "#1A1535" }}>I am using SignAI as… <span style={{ color: "#C4B0FF", fontWeight: 400 }}>(optional)</span></label>
                  <div className="flex flex-wrap gap-2">
                    {roles.map(r => (
                      <button type="button" key={r}
                        onClick={() => set("role")(form.role === r ? "" : r)}
                        className="px-3 py-2 rounded-xl text-xs font-medium transition-all"
                        style={{
                          background: form.role === r ? "#6C47FF" : "#F5F4FF",
                          color: form.role === r ? "white" : "#7B7BA0",
                          border: `1px solid ${form.role === r ? "#6C47FF" : "#E2E0F8"}`,
                        }}>
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Terms */}
                <div>
                  <label className="flex items-start gap-3 cursor-pointer select-none">
                    <div
                      className="flex-shrink-0 mt-0.5 rounded-lg flex items-center justify-center transition-all"
                      style={{ width: 20, height: 20, background: form.agree ? "#6C47FF" : "white", border: `2px solid ${errors.agree ? "#EF4444" : form.agree ? "#6C47FF" : "#E2E0F8"}` }}
                      onClick={() => set("agree")(!form.agree)}
                    >
                      {form.agree && <Check size={12} color="white" strokeWidth={3} />}
                    </div>
                    <span className="text-sm leading-relaxed" style={{ color: "#7B7BA0" }}>
                      I agree to the{" "}
                      <span className="font-semibold cursor-pointer" style={{ color: "#6C47FF" }}>Terms of Service</span>
                      {" "}and{" "}
                      <span className="font-semibold cursor-pointer" style={{ color: "#6C47FF" }}>Privacy Policy</span>
                    </span>
                  </label>
                  {errors.agree && <p className="text-xs mt-1 ml-8 font-medium" style={{ color: "#EF4444" }}>{errors.agree}</p>}
                </div>


                {serverError && (
                <p
                    className="text-sm text-center font-medium"
                    style={{ color: "#EF4444" }}
                  >
                    {serverError}
                </p>
                )}
                
                {/* Submit */}
                <button type="submit"
                  className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold text-base transition-all hover:scale-[1.02] hover:shadow-lg mt-1"
                  style={{ background: "linear-gradient(135deg, #6C47FF 0%, #9D7BFF 100%)", color: "white", fontFamily: "Nunito, sans-serif" }}>
                  Create my account <ArrowRight size={18} />
                </button>

                {/* Sign in link */}
                <p className="text-sm text-center" style={{ color: "#7B7BA0" }}>
                  Already have an account?{" "}
                  <span
                    onClick={() => navigate("/signin")}
                    className="font-semibold cursor-pointer hover:underline"
                    style={{ color: "#6C47FF" }}
                  >
                    Sign in
                  </span>
                </p>
              
              
              
              
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

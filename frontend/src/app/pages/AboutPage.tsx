import { motion } from "motion/react";
import { useNavigate } from "react-router";
import { Hand, Zap, Globe, Heart, Users, BookOpen, Award, ArrowRight } from "lucide-react";

const team = [
  { name: "Yomn Toumia", role: "AI Research Intern", emoji: "👩‍💻", bio: "Engineering student at ENSI, contributing to AI research and developing machine learning solutions at Artificial Insight." },
  { name: "Amal Ktiti", role: "AI Research Intern", emoji: "👩‍💻", bio: "Engineering student at FSB, exploring artificial intelligence research and building innovative AI solutions at Artificial Insight." },
  { name: "Saddam Zemmali", role: "Mentor & Artificial Insight's CEO", emoji: "🧑‍💼", bio: "Leading Artificial Insight and mentoring teams in building scalable AI solutions and real-time machine learning systems." },
  { name: "Mayssa Namsi", role: "Mentor & Artificial Insight's Cloud Engineer ", emoji: "🧑‍💻", bio: "Cloud Engineer specializing in designing scalable cloud infrastructures, deploying reliable systems, and supporting AI applications." },
];

const stats = [
  { value: "2000+", label: "Signs supported", icon: Hand },
  { value: "63.2%", label: "Detection accuracy", icon: Zap },
  { value: "30ms", label: "Average response", icon: Award },
  { value: "1 country", label: "Active users from", icon: Globe },
];

const timeline = [
  { Month: "June", title: "The idea", desc: "Started as a research project to bridge the communication gap for the Deaf community." },
  { Month: "July", title: "First model", desc: "Launched our first sign recognition model trained on 50,000 video samples from Deaf volunteers." },
  { Month: "August", title: "Dataset", desc: "Expanded to 500 signs using the WLASL dataset." },
  { Month: "Now", title: "Bidirectional", desc: "Added Text→Sign generation, letting anyone learn or communicate through the app." },
];

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, ease: "easeOut", delay }}>
      {children}
    </motion.div>
  );
}

export default function AboutPage() {
  const navigate = useNavigate();

  return (
    <div className="flex-1 flex flex-col" style={{ fontFamily: "Inter, sans-serif" }}>
      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="px-6 md:px-16 pt-16 pb-20 text-center relative overflow-hidden">
        {/* Background blob */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div style={{ width: 600, height: 400, background: "radial-gradient(ellipse, rgba(108,71,255,0.12) 0%, transparent 70%)", borderRadius: "50%" }} />
        </div>

        <FadeIn>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold mb-8"
            style={{ background: "#EEF0FF", color: "#6C47FF", border: "1px solid #E2E0F8" }}>
            <Heart size={12} /> Our mission
          </div>
          <h1 className="font-black text-5xl md:text-6xl mb-6 leading-tight"
            style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif", letterSpacing: "-0.03em" }}>
            Breaking the silence<br />
            <span style={{ color: "#6C47FF" }}>one sign at a time</span>
          </h1>
          <p className="text-lg max-w-2xl mx-auto leading-relaxed" style={{ color: "#7B7BA0" }}>
            EchoSign was built to make communication accessible for everyone : whether you're Deaf, learning sign language,
            or simply want to connect across language barriers.
          </p>
        </FadeIn>
      </section>

      {/* ── Stats ────────────────────────────────────────────────────────────── */}
      <section className="px-6 md:px-16 pb-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map(({ value, label, icon: Icon }, i) => (
            <FadeIn key={label} delay={i * 0.08}>
              <div className="rounded-2xl p-6 text-center" style={{ background: "#FFFFFF", border: "1px solid #E2E0F8" }}>
                <div className="flex justify-center mb-3">
                  <div className="rounded-xl flex items-center justify-center" style={{ width: 40, height: 40, background: "#EEF0FF" }}>
                    <Icon size={18} color="#6C47FF" />
                  </div>
                </div>
                <div className="font-black text-2xl mb-1" style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif" }}>{value}</div>
                <div className="text-xs font-medium" style={{ color: "#7B7BA0" }}>{label}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────────────── */}
      <section className="px-6 md:px-16 pb-16">
        <FadeIn>
          <div className="rounded-3xl p-10 md:p-14" style={{ background: "#FFFFFF", border: "1px solid #E2E0F8" }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold mb-6"
              style={{ background: "#EEF0FF", color: "#6C47FF" }}>
              <BookOpen size={12} /> How it works
            </div>
            <h2 className="font-black text-3xl mb-10" style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif", letterSpacing: "-0.02em" }}>
              Two ways to use EchoSign
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              {[
                {
                  num: "01",
                  title: "Sign → Text",
                  color: "#6C47FF",
                  bg: "#EEF0FF",
                  steps: [
                    "Your camera captures your hand in real time",
                    "MediaPipe extracts landmarks per frame",
                    "Modeel classifies the gesture across 2,000 signs",
                    "The detected word appears with a confidence score",
                  ],
                },
                {
                  num: "02",
                  title: "Text → Sign",
                  color: "#10B981",
                  bg: "#D1FAE5",
                  steps: [
                    "You type any word or short phrase",
                    "Our pipeline tokenizes and maps to ASL gloss",
                    "The 3D avatar renders the fingerspelling sequence",
                    "You can slow down, pause, or step letter by letter",
                  ],
                },
              ].map(({ num, title, color, bg, steps }) => (
                <div key={num}>
                  <div className="flex items-center gap-3 mb-5">
                    <span className="font-black text-3xl" style={{ color, fontFamily: "Nunito, sans-serif" }}>{num}</span>
                    <div className="h-px flex-1" style={{ background: "#E2E0F8" }} />
                    <span className="px-3 py-1 rounded-full text-sm font-semibold" style={{ background: bg, color }}>{title}</span>
                  </div>
                  <ol className="flex flex-col gap-3">
                    {steps.map((s, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm leading-relaxed" style={{ color: "#7B7BA0" }}>
                        <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold mt-0.5"
                          style={{ background: bg, color }}>
                          {i + 1}
                        </span>
                        {s}
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>
      </section>

      {/* ── Timeline ─────────────────────────────────────────────────────────── */}
      <section className="px-6 md:px-16 pb-16">
        <FadeIn>
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold mb-4"
              style={{ background: "#EEF0FF", color: "#6C47FF" }}>
              <Award size={12} /> Our journey
            </div>
            <h2 className="font-black text-3xl" style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif", letterSpacing: "-0.02em" }}>
              From idea to impact
            </h2>
          </div>
        </FadeIn>

        <div className="relative pl-8 flex flex-col gap-0">
          <div className="absolute left-3 top-2 bottom-2 w-0.5" style={{ background: "#E2E0F8" }} />
          {timeline.map(({ Month, title, desc }, i) => (
            <FadeIn key={Month} delay={i * 0.07}>
              <div className="relative pb-8">
                <div className="absolute -left-5 top-1 w-4 h-4 rounded-full border-2 border-white"
                  style={{ background: i === timeline.length - 1 ? "#6C47FF" : "#C4B0FF" }} />
                <div className="text-xs font-bold mb-1" style={{ color: "#6C47FF" }}>{Month}</div>
                <div className="font-semibold text-base mb-1" style={{ color: "#1A1535" }}>{title}</div>
                <div className="text-sm leading-relaxed" style={{ color: "#7B7BA0" }}>{desc}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ── Team ─────────────────────────────────────────────────────────────── */}
      <section className="px-6 md:px-16 pb-16">
        <FadeIn>
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold mb-4"
              style={{ background: "#EEF0FF", color: "#6C47FF" }}>
              <Users size={12} /> The team
            </div>
            <h2 className="font-black text-3xl" style={{ color: "#1A1535", fontFamily: "Nunito, sans-serif", letterSpacing: "-0.02em" }}>
              People behind EchoSign
            </h2>
          </div>
        </FadeIn>

        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-5">
          {team.map(({ name, role, emoji, bio }, i) => (
            <FadeIn key={name} delay={i * 0.07}>
              <div className="rounded-2xl p-6 flex flex-col gap-3 h-full" style={{ background: "#FFFFFF", border: "1px solid #E2E0F8" }}>
                <div className="text-4xl">{emoji}</div>
                <div>
                  <div className="font-bold text-base" style={{ color: "#1A1535" }}>{name}</div>
                  <div className="text-xs font-medium mt-0.5" style={{ color: "#6C47FF" }}>{role}</div>
                </div>
                <div className="text-sm leading-relaxed" style={{ color: "#7B7BA0" }}>{bio}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="px-6 md:px-16 pb-16">
        <FadeIn>
          <div className="rounded-3xl px-10 py-12 text-center" style={{ background: "linear-gradient(135deg, #6C47FF 0%, #9D7BFF 100%)" }}>
            <h2 className="font-black text-3xl text-white mb-3" style={{ fontFamily: "Nunito, sans-serif" }}>
              Ready to get started?
            </h2>
            <p className="text-white opacity-80 mb-8 text-base">
              Join thousands of people using SignAI to communicate, learn, and connect.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button onClick={() => navigate("/signup")}
                className="flex items-center gap-2 px-8 py-3.5 rounded-2xl font-semibold text-sm transition-all hover:scale-105"
                style={{ background: "white", color: "#6C47FF" }}>
                Create a free account <ArrowRight size={16} />
              </button>
              <button onClick={() => navigate("/Detect")}
                className="flex items-center gap-2 px-8 py-3.5 rounded-2xl font-semibold text-sm transition-all hover:bg-white/10"
                style={{ border: "2px solid rgba(255,255,255,0.5)", color: "white" }}>
                Try without signing up
              </button>
            </div>
          </div>
        </FadeIn>
      </section>
    </div>
  );
}

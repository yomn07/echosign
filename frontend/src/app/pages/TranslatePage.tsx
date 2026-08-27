import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Search,
  ArrowRight,
  Volume2,
  RotateCcw,
  MapPin,
  Zap,
  Check,
} from "lucide-react";
import { puter } from "@heyputer/puter.js";
import idx2gloss from "../../idx2gloss_cache.json";
import LandmarkPlayer from "../components/ui/LandmarkPlayerV";

const GLOSS_DICT = new Set(
  Object.values(idx2gloss).map(
    (word) => word.toUpperCase()
  )
);


// ─── Fingerspell Avatar ──────────────────────────────────────────────────────
function LetterLandmarkPlayer({
  letter,
  playing,
}: {
  letter: string;
  playing: boolean;
}) {
  return (
    <LandmarkPlayer
      key={letter}
      word={letter.toUpperCase()}
      playing={playing}
    />
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TranslatePage() {
  const [input, setInput] = useState("");

  const [sourceLanguage, setSourceLanguage] =
    useState("en");

  const [glossWords, setGlossWords] =
    useState<string[]>([]);

  const [currentWord, setCurrentWord] =
    useState(0);

  const [currentLetter, setCurrentLetter] =
    useState(0);

  const [playing, setPlaying] =
    useState(false);

  const [speed, setSpeed] =
    useState(700);

  const [loading, setLoading] =
    useState(false);

  const [translatedEnglish, setTranslatedEnglish] =
    useState("");

  const current =
    glossWords[currentWord] ?? "";

  const word = current
    .toUpperCase()
    .replace(/[^A-Z]/g, "");

  const isKnown =
    GLOSS_DICT.has(current);

  const letters = word
    .split("")
    .filter((c) => c !== " ");

  const startPlaying = () => {
    if (
      letters.length > 0 ||
      isKnown
    ) {
      setCurrentLetter(0);
      setPlaying(true);
    }
  };

  const stopPlaying = () =>
    setPlaying(false);


  const translateToEnglish = async (
    text: string
  ): Promise<string> => {
    // English 't need translation
    if (sourceLanguage === "en") {
      return text;
    }

    const languageNames: Record<string, string> = {
      fr: "French",
      ar: "Arabic",
      es: "Spanish",
      de: "German",
      it: "Italian",
      pt: "Portuguese",
      tr: "Turkish",
      en: "English",
    };

    const sourceName =
      languageNames[sourceLanguage] ??
      sourceLanguage;

    const prompt = `
Translate the following ${sourceName} text into natural English.

IMPORTANT:
- Preserve the complete meaning.
- Do not summarize.
- Do not remove names.
- Do not remove words.
- Keep the translation faithful to the original.
- Return ONLY the English translation.
- Do not add explanations or quotation marks.

Text:
${text}
`;

    const response = await puter.ai.chat(prompt, {
      model: "gpt-5.4-nano",
    });

    // Puter can return the completion directly
    // or an object containing message.content.
    let translation = "";

    if (typeof response === "string") {
      translation = response;
    } else if (
      response &&
      typeof response === "object" &&
      "message" in response
    ) {
      const message = (
        response as {
          message?: {
            content?: unknown;
          };
        }
      ).message;

      if (typeof message?.content === "string") {
        translation = message.content;
      } else if (
        Array.isArray(message?.content)
      ) {
        translation = message.content
          .map((part) =>
            typeof part === "string"
              ? part
              : typeof part === "object" &&
                part !== null &&
                "text" in part
              ? String(
                  (
                    part as {
                      text?: unknown;
                    }
                  ).text ?? ""
                )
              : ""
          )
          .join("");
      }
    }
    if (!translation || typeof translation !== "string") {
  throw new Error("Translation result is empty or invalid");
}
    translation = translation
      .trim()
      .replace(/^["']|["']$/g, "");

    if (!translation) {
      throw new Error(
        "Puter returned an empty translation"
      );
    }

    return translation;
  };


  const translateEnglishToGloss = async (
    englishText: string
  ): Promise<string> => {
    const response = await fetch(
      "http://127.0.0.1:8000/translate",
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          text: englishText,
        }),
      }
    );

    if (!response.ok) {
      const errorData =
        await response.json().catch(() => ({}));

      throw new Error(
        errorData.detail ||
          "ASL gloss translation failed"
      );
    }

    const data = await response.json();

    return data.gloss;
  };

  // ─────────────────────────────────────────
  // Submit
  // ─────────────────────────────────────────

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    if (!input.trim()) return;

    setLoading(true);
    setPlaying(false);

    try {
      // 1. User language → English
      const englishText =
        await translateToEnglish(
          input.trim()
        );

      console.log(
        "English translation:",
        englishText
      );

      setTranslatedEnglish(
        englishText
      );

      // 2. English → ASL Gloss
      const gloss =
        await translateEnglishToGloss(
          englishText
        );

      console.log(
        "ASL gloss:",
        gloss
      );

      // 3. Gloss → words
      const words = gloss
        .trim()
        .toUpperCase()
        .split(/\s+/);

      setGlossWords(words);
      setCurrentWord(0);
      setCurrentLetter(0);
      setPlaying(true);

    } catch (error) {
      console.error(
        "Translation error:",
        error
      );

      alert(
        error instanceof Error
          ? error.message
          : "Translation failed"
      );

    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────
  // Fingerspell / sign animation
  // ─────────────────────────────────────────

  useEffect(() => {
    if (!playing) return;

    if (isKnown) {
      const timer = setTimeout(() => {
        if (
          currentWord <
          glossWords.length - 1
        ) {
          setCurrentWord(
            (prev) => prev + 1
          );

          setCurrentLetter(0);

        } else {
          setPlaying(false);
        }
      }, 2000);

      return () =>
        clearTimeout(timer);
    }

    if (letters.length === 0)
      return;

    const timer = setInterval(() => {
      setCurrentLetter((prev) => {
        if (
          prev <
          letters.length - 1
        ) {
          return prev + 1;
        }

        if (
          currentWord <
          glossWords.length - 1
        ) {
          setCurrentWord(
            (word) => word + 1
          );

          return 0;

        } else {
          setPlaying(false);

          return 0;
        }
      });
    }, speed);

    return () =>
      clearInterval(timer);

  }, [
    playing,
    isKnown,
    letters.length,
    currentWord,
    glossWords.length,
    speed,
  ]);

  // ─────────────────────────────────────────
  // Quick picks
  // ─────────────────────────────────────────

  const handleQuickPick = async (
    text: string
  ) => {
    setInput(text);

    setLoading(true);
    setPlaying(false);

    try {
      const englishText =
        await translateToEnglish(text);

      setTranslatedEnglish(
        englishText
      );

      const gloss =
        await translateEnglishToGloss(
          englishText
        );

      const words = gloss
        .trim()
        .toUpperCase()
        .split(/\s+/);

      setGlossWords(words);
      setCurrentWord(0);
      setCurrentLetter(0);
      setPlaying(true);

    } catch (error) {
      console.error(
        "Quick pick translation error:",
        error
      );

      alert(
        error instanceof Error
          ? error.message
          : "Translation failed"
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 px-6 md:px-8 py-8 flex flex-col gap-8 max-w-5xl mx-auto w-full">

      {/* Heading */}

      <div>
        <h1
          className="font-black text-4xl mb-2"
          style={{
            color: "#1A1535",
            fontFamily:
              "Nunito, sans-serif",
            letterSpacing: "-0.02em",
          }}
        >
          Sign a Word
        </h1>

        <p
          className="text-base"
          style={{ color: "#7B7BA0" }}
        >
          Type a phrase in your language
          and see it translated into ASL.
        </p>
      </div>

      {/* Translation form */}

      <form
        onSubmit={handleSubmit}
        className="rounded-3xl p-3 shadow-sm"
        style={{
          background: "#FFFFFF",
          border: "1px solid #E2E0F8",
        }}
      >
        <div className="flex flex-col md:flex-row gap-3">

          {/* Language */}

          <div
            className="flex items-center gap-2 px-4 rounded-2xl md:min-w-[170px]"
            style={{
              background: "#F8F7FF",
              border:
                "1px solid #E2E0F8",
            }}
          >
            <span
              className="text-xs font-semibold uppercase tracking-wide"
              style={{
                color: "#9D7BFF",
              }}
            >
              From
            </span>

            <select
              value={sourceLanguage}
              onChange={(e) =>
                setSourceLanguage(
                  e.target.value
                )
              }
              className="flex-1 bg-transparent outline-none text-sm font-semibold cursor-pointer"
              style={{
                color: "#1A1535",
              }}
            >
              <option value="en">
                English
              </option>

              <option value="fr">
                French
              </option>

              <option value="ar">
                Arabic
              </option>

              <option value="es">
                Spanish
              </option>

              <option value="de">
                German
              </option>

              <option value="it">
                Italian
              </option>

              <option value="pt">
                Portuguese
              </option>

              <option value="tr">
                Turkish
              </option>
            </select>
          </div>

          {/* Input */}

          <div className="flex-1 relative">
            <Search
              size={18}
              color="#C4B0FF"
              className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none"
            />

            <input
              type="text"
              value={input}
              onChange={(e) =>
                setInput(e.target.value)
              }
              placeholder="Type a phrase, e.g. Hello..."
              disabled={loading}
              className="w-full pl-11 pr-4 py-4 rounded-2xl text-base font-medium outline-none transition-all"
              style={{
                background: "#F8F7FF",
                border:
                  "1px solid #E2E0F8",
                color: "#1A1535",
              }}
            />
          </div>

          {/* Submit */}

          <button
            type="submit"
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-semibold text-sm transition-all hover:scale-[1.02] disabled:opacity-50"
            style={{
              background: "#6C47FF",
              color: "white",
              boxShadow:
                "0 6px 18px rgba(108,71,255,0.20)",
            }}
          >
            {loading
              ? "Translating..."
              : "Show Sign"}

            {!loading && (
              <ArrowRight size={16} />
            )}
          </button>
        </div>

        {/* Pipeline indicator */}

        <div className="flex items-center gap-2 px-2 pt-3">
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: "#6C47FF",
            }}
          />

          <span
            className="text-xs font-medium"
            style={{
              color: "#9A99B8",
            }}
          >
            {sourceLanguage === "en"
              ? "English → ASL"
              : `${sourceLanguage.toUpperCase()} → English → ASL`}
          </span>
        </div>
      </form>

      {/* Quick picks */}

      <div className="flex flex-wrap items-center gap-2">
        <span
          className="text-sm font-medium mr-1"
          style={{
            color: "#7B7BA0",
          }}
        >
          Try:
        </span>
      </div>

      {/* Translated English */}

      {translatedEnglish &&
        sourceLanguage !== "en" && (
          <div
            className="rounded-2xl px-5 py-4"
            style={{
              background: "#F8F7FF",
              border:
                "1px solid #E2E0F8",
            }}
          >
            <p
              className="text-xs font-semibold mb-1"
              style={{
                color: "#9D7BFF",
              }}
            >
              English translation
            </p>

            <p
              className="text-sm font-medium"
              style={{
                color: "#1A1535",
              }}
            >
              {translatedEnglish}
            </p>
          </div>
        )}

      {/* Result */}

      <AnimatePresence mode="wait">
        {glossWords.length > 0 && (
          <motion.div
            key={currentWord}
            initial={{
              opacity: 0,
              y: 16,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              y: -8,
            }}
            transition={{
              duration: 0.25,
              ease: "easeOut",
            }}
            className="grid gap-6"
            style={{
              gridTemplateColumns:
                "1fr 1fr",
            }}
          >

            {/* Avatar */}

            <div
              className="rounded-3xl overflow-hidden shadow-sm"
              style={{
                background: "#020523",
                border:
                  "1px solid #E2E0F8",
                minHeight: 340,
              }}
            >
              {isKnown ? (
                <LandmarkPlayer
                  word={current}
                  playing={playing}
                />
              ) : letters.length > 0 ? (
                <LetterLandmarkPlayer
                  key={`${currentWord}-${currentLetter}`}
                  letter={letters[currentLetter]}
                  playing={playing}
                />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-white text-sm opacity-40">
                    Nothing to show
                  </p>
                </div>
              )}
            </div>

            {/* Info */}

            <div className="flex flex-col gap-4">

              <div
                className="rounded-3xl p-7 shadow-sm"
                style={{
                  background: "#FFFFFF",
                  border:
                    "1px solid #E2E0F8",
                }}
              >
                <p
                  className="text-sm font-medium mb-3"
                  style={{
                    color: "#7B7BA0",
                  }}
                >
                  Showing sign for
                </p>

                <div
                  className="font-black leading-none mb-4"
                  style={{
                    fontSize:
                      word.length > 9
                        ? 38
                        : word.length > 5
                        ? 50
                        : 30,

                    color: "#1A1535",

                    fontFamily:
                      "Nunito, sans-serif",

                    letterSpacing:
                      "-0.02em",
                  }}
                >
                  {glossWords.map(
                    (w, i) => (
                      <span
                        key={i}
                        style={{
                          marginRight:
                            "8px",

                          color:
                            i === currentWord
                              ? "#6C47FF"
                              : "#1A1535",
                        }}
                      >
                        {w}
                      </span>
                    )
                  )}
                </div>

                <div className="flex items-center gap-2 flex-wrap">

                  <span
                    className="text-xs font-semibold px-3 py-1 rounded-full"
                    style={{
                      background:
                        isKnown
                          ? "#D1FAE5"
                          : "#EEF0FF",

                      color:
                        isKnown
                          ? "#10B981"
                          : "#6C47FF",
                    }}
                  >
                    {isKnown
                      ? "✓ Full ASL sign"
                      : "Finger spelling"}
                  </span>

                  {isKnown && (
                    <span
                      className="text-xs font-semibold px-3 py-1 rounded-full"
                      style={{
                        background:
                          "#EEF0FF",

                        color:
                          "#6C47FF",
                      }}
                    >
                      WLASL-2000 dataset
                    </span>
                  )}
                </div>

                <div
                  className="mt-4 p-3 rounded-xl text-xs leading-relaxed"
                  style={{
                    background:
                      "#F5F4FF",
                    color:
                      "#7B7BA0",
                  }}
                >
                  {isKnown
                    ? "This word has a dedicated ASL sign. The hand animates between the two key poses of the sign."
                    : "This word isn't in our sign dictionary yet. We're showing you how to fingerspell it letter by letter in ASL."}
                </div>
              </div>

              {/* Letter tiles */}

              {!isKnown &&
                letters.length > 0 && (
                  <div
                    className="rounded-3xl p-6 shadow-sm"
                    style={{
                      background:
                        "#FFFFFF",
                      border:
                        "1px solid #E2E0F8",
                    }}
                  >
                    <p
                      className="text-sm font-medium mb-4"
                      style={{
                        color:
                          "#7B7BA0",
                      }}
                    >
                      Tap a letter to jump
                      to it
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {letters.map(
                        (l, i) => (
                          <button
                            key={`${l}-${i}`}
                            onClick={() => {
                              stopPlaying();

                              setCurrentLetter(
                                i
                              );
                            }}
                            className="w-9 h-9 rounded-xl font-bold text-sm transition-all hover:scale-110"
                            style={{
                              background:
                                i ===
                                currentLetter
                                  ? "#6C47FF"
                                  : "#EEF0FF",

                              color:
                                i ===
                                currentLetter
                                  ? "white"
                                  : "#6C47FF",

                              fontFamily:
                                "Nunito, sans-serif",

                              boxShadow:
                                i ===
                                currentLetter
                                  ? "0 2px 12px rgba(108,71,255,0.35)"
                                  : "none",
                            }}
                          >
                            {l}
                          </button>
                        )
                      )}
                    </div>
                  </div>
                )}

              {/* Playback */}

              <div
                className="rounded-3xl p-6 shadow-sm flex flex-col gap-4"
                style={{
                  background:
                    "#FFFFFF",
                  border:
                    "1px solid #E2E0F8",
                }}
              >
                <p
                  className="text-sm font-medium"
                  style={{
                    color:
                      "#7B7BA0",
                  }}
                >
                  Playback
                </p>

                <div className="flex items-center gap-3">

                  <button
                    onClick={
                      playing
                        ? stopPlaying
                        : startPlaying
                    }
                    disabled={
                      !isKnown &&
                      letters.length === 0
                    }
                    className="flex items-center gap-2 px-5 py-2.5 rounded-2xl font-semibold text-sm transition-all hover:scale-105 disabled:opacity-40"
                    style={{
                      background:
                        playing
                          ? "#EEF0FF"
                          : "#6C47FF",

                      color:
                        playing
                          ? "#6C47FF"
                          : "white",
                    }}
                  >
                    <Volume2 size={16} />

                    {playing
                      ? "Pause"
                      : isKnown
                      ? "Animate Sign"
                      : "Animate Letters"}
                  </button>

                  <button
                    onClick={() => {
                      stopPlaying();
                      setCurrentLetter(
                        0
                      );
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-2xl font-medium text-sm transition-all"
                    style={{
                      border:
                        "1px solid #E2E0F8",
                      color:
                        "#7B7BA0",
                    }}
                  >
                    <RotateCcw
                      size={14}
                    />

                    Reset
                  </button>
                </div>

                <div>
                  <div
                    className="flex justify-between text-xs mb-2"
                    style={{
                      color:
                        "#7B7BA0",
                    }}
                  >
                    <span>
                      Speed
                    </span>

                    <span>
                      {speed <= 350
                        ? "Fast"
                        : speed <= 700
                        ? "Normal"
                        : "Slow"}
                    </span>
                  </div>

                  <input
                    type="range"
                    min={200}
                    max={1400}
                    step={100}
                    value={speed}
                    onChange={(e) =>
                      setSpeed(
                        Number(
                          e.target.value
                        )
                      )
                    }
                    className="w-full accent-[#6C47FF]"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}

      {glossWords.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <div className="text-5xl">
            👆
          </div>

          <p
            className="text-base font-medium"
            style={{
              color: "#C4B0FF",
            }}
          >
            Type a phrase above to see
            its sign
          </p>
        </div>
      )}
    </div>
  );
}


import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  motion,
  AnimatePresence,
} from "motion/react";

import {
  CheckCircle,
  XCircle,
  Hand,
  Circle,
  Check,
  Volume2,
  RotateCcw,
} from "lucide-react";

import Webcam from "react-webcam";

import { puter } from "@heyputer/puter.js";

import CameraOverlay from "../components/ui/CameraOverlay";
import TopFiveList from "../components/ui/TopFiveList";


// ============================================================
// TYPES
// ============================================================

type DetectState =
  | "idle"
  | "recording"
  | "result"
  | "confirmed";

type Candidate = {
  word: string;
  conf: number;
};

type Landmarks = {
  left_hand: [number, number][];
  right_hand: [number, number][];
  pose: [number, number][];
};

type TrialStatus = {
  trial_id?: string;

  trials_remaining?: number | null;

  trial_used?: boolean;

  requires_login?: boolean;

  authenticated?: boolean;

  user?: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
  };
};


// ============================================================
// LANGUAGES
// ============================================================

const LANGUAGES = [
  {
    code: "en",
    name: "English",
    speech: "en-US",
  },
  {
    code: "fr",
    name: "French",
    speech: "fr-FR",
  },
  {
    code: "ar",
    name: "Arabic",
    speech: "ar-AE",
  },
  {
    code: "es",
    name: "Spanish",
    speech: "es-ES",
  },
  {
    code: "de",
    name: "German",
    speech: "de-DE",
  },
  {
    code: "it",
    name: "Italian",
    speech: "it-IT",
  },
  {
    code: "pt",
    name: "Portuguese",
    speech: "pt-PT",
  },
  {
    code: "tr",
    name: "Turkish",
    speech: "tr-TR",
  },
];

const languageNames: Record<string, string> = {
  en: "English",
  fr: "French",
  ar: "Arabic",
  es: "Spanish",
  de: "German",
  it: "Italian",
  pt: "Portuguese",
  tr: "Turkish",
};


// ============================================================
// WEBSOCKET URL
// ============================================================

function getWebSocketUrl() {
  const protocol =
    window.location.protocol === "https:"
      ? "wss:"
      : "ws:";

  return `${protocol}//${window.location.host}/ws/sign`;
}


// ============================================================
// ANIMATED NUMBER
// ============================================================

function useAnimatedNumber(
  target: number,
  duration = 450
) {
  const [value, setValue] =
    useState(target);

  const previous =
    useRef(target);

  useEffect(() => {
    const start =
      previous.current;

    const startTime =
      performance.now();

    let frame = 0;

    function animate(now: number) {
      const progress =
        Math.min(
          (now - startTime) / duration,
          1
        );

      const eased =
        1 -
        Math.pow(
          1 - progress,
          3
        );

      setValue(
        start +
          (target - start) *
            eased
      );

      if (progress < 1) {
        frame =
          requestAnimationFrame(
            animate
          );
      } else {
        previous.current =
          target;
      }
    }

    frame =
      requestAnimationFrame(
        animate
      );

    return () =>
      cancelAnimationFrame(
        frame
      );
  }, [
    target,
    duration,
  ]);

  return value;
}


// ============================================================
// PAGE
// ============================================================

export default function HomePage() {

  // ==========================================================
  // REFS
  // ==========================================================

  const webcamRef =
    useRef<Webcam>(null);

  const socketRef =
    useRef<WebSocket | null>(null);

  const reconnectTimerRef =
    useRef<number | null>(null);

  const mountedRef =
    useRef(true);

  const stoppedRef =
    useRef(false);

  const detectStateRef =
    useRef<DetectState>("idle");

  const authenticatedRef =
    useRef(false);

  const requiresLoginRef =
    useRef(false);

  // Prevent double consumption if the user
  // somehow clicks Yes multiple times quickly.
  const consumingTrialRef =
    useRef(false);


  // ==========================================================
  // DETECTION
  // ==========================================================

  const [
    detectState,
    setDetectState,
  ] =
    useState<DetectState>("idle");


  useEffect(() => {
    detectStateRef.current =
      detectState;
  }, [
    detectState,
  ]);


  // ==========================================================
  // CONNECTION
  // ==========================================================

  const [
    connected,
    setConnected,
  ] =
    useState(false);


  // ==========================================================
  // AUTHENTICATION
  // ==========================================================

  const [
    authenticated,
    setAuthenticatedState,
  ] =
    useState(false);


  function updateAuthenticated(
    value: boolean
  ) {
    authenticatedRef.current =
      value;

    setAuthenticatedState(
      value
    );
  }


  // ==========================================================
  // TRIAL
  // ==========================================================

  const [
    trialsRemaining,
    setTrialsRemaining,
  ] =
    useState<number | null>(null);


  const [
    requiresLogin,
    setRequiresLoginState,
  ] =
    useState(false);


  function updateRequiresLogin(
    value: boolean
  ) {
    requiresLoginRef.current =
      value;

    setRequiresLoginState(
      value
    );
  }


  // ==========================================================
  // DETECTION DATA
  // ==========================================================

  const [
    landmarks,
    setLandmarks,
  ] =
    useState<Landmarks | null>(
      null
    );


  const [
    confidence,
    setConfidence,
  ] =
    useState(0);


  const [
    detectedWord,
    setDetectedWord,
  ] =
    useState("Waiting...");


  const [
    candidates,
    setCandidates,
  ] =
    useState<Candidate[]>([]);


  // ==========================================================
  // SENTENCE
  // ==========================================================

  const [
    sentence,
    setSentence,
  ] =
    useState<string[]>([]);


  // ==========================================================
  // TRANSLATION
  // ==========================================================

  const [
    targetLanguage,
    setTargetLanguage,
  ] =
    useState("en");


  const [
    translatedWord,
    setTranslatedWord,
  ] =
    useState("");


  const [
    translatedSentence,
    setTranslatedSentence,
  ] =
    useState("");


  const [
    translationLoading,
    setTranslationLoading,
  ] =
    useState(false);


  const [
    sentenceTranslationLoading,
    setSentenceTranslationLoading,
  ] =
    useState(false);


  const [
    translationError,
    setTranslationError,
  ] =
    useState("");


  const [
    sentenceTranslationError,
    setSentenceTranslationError,
  ] =
    useState("");


  const word =
    detectedWord;


  const animConf =
    useAnimatedNumber(
      confidence * 100
    );


  // ==========================================================
  // GET TRIAL STATUS
  //
  // IMPORTANT:
  //
  // This does NOT consume a trial.
  //
  // It only reads the current trial count from
  // the backend.
  //
  // credentials: include is important because
  // the anonymous trial is associated with a cookie.
  // ==========================================================

  async function getTrialStatus(): Promise<TrialStatus> {

    const token =
      sessionStorage.getItem(
        "access_token"
      );


    const response =
      await fetch(
        "/api/trial/status",
        {
          method: "GET",

          credentials: "include",

          headers: {
            Accept:
              "application/json",

            ...(token
              ? {
                  Authorization:
                    `Bearer ${token}`,
                }
              : {}),
          },
        }
      );


    if (!response.ok) {
      throw new Error(
        `Trial status failed: ${response.status}`
      );
    }


    const trial =
      (await response.json()) as TrialStatus;


    const isAuthenticated =
      trial.authenticated === true;


    updateAuthenticated(
      isAuthenticated
    );


    if (isAuthenticated) {

      // Logged-in users have unlimited trials.
      setTrialsRemaining(
        null
      );

      updateRequiresLogin(
        false
      );

    } else {

      // Anonymous user.
      //
      // IMPORTANT:
      // Always use the backend value.
      setTrialsRemaining(
        typeof trial.trials_remaining ===
          "number"
          ? trial.trials_remaining
          : null
      );

      updateRequiresLogin(
        trial.requires_login === true
      );
    }


    return trial;
  }


  // ==========================================================
  // CONSUME ONE TRIAL
  //
  // THIS IS THE IMPORTANT FIX.
  //
  // The frontend must call:
  //
  // POST /api/trial/consume
  //
  // when an anonymous user confirms a sign.
  // ==========================================================

  async function consumeAnonymousTrial(): Promise<TrialStatus> {

    const response =
      await fetch(
        "/api/trial/consume",
        {
          method: "POST",

          credentials: "include",

          headers: {
            Accept:
              "application/json",
          },
        }
      );


    if (!response.ok) {

      let message =
        "Unable to consume trial.";

      try {

        const error =
          await response.json();

        if (
          error?.detail?.message
        ) {
          message =
            error.detail.message;
        }

      } catch {
        // Ignore JSON parsing errors.
      }

      throw new Error(
        message
      );
    }


    const result =
      (await response.json()) as TrialStatus;


    // Immediately update the UI.
    if (
      typeof result.trials_remaining ===
      "number"
    ) {

      setTrialsRemaining(
        result.trials_remaining
      );
    }


    updateRequiresLogin(
      result.requires_login === true
    );


    return result;
  }


  // ==========================================================
  // TRANSLATION
  // ==========================================================

  async function translateFromEnglish(
    text: string
  ): Promise<string> {

    if (!text.trim()) {
      return "";
    }


    if (
      targetLanguage === "en"
    ) {
      return text;
    }


    const targetName =
      languageNames[
        targetLanguage
      ] ??
      targetLanguage;


    const prompt = `
Translate the following English text into natural ${targetName}.

IMPORTANT:
- Preserve the complete meaning.
- Do not summarize.
- Do not remove names.
- Do not remove words.
- Keep the translation faithful.
- Use natural grammar.
- Do not add explanations.
- Return ONLY the translation.
- Do not use quotation marks.

English text:
${text}
`;


    const response =
      await puter.ai.chat(
        prompt,
        {
          model:
            "gpt-5.4-nano",
        }
      );


    let translation = "";


    if (
      typeof response ===
      "string"
    ) {

      translation =
        response;

    } else if (
      response &&
      typeof response ===
        "object" &&
      "message" in response
    ) {

      const message =
        (
          response as {
            message?: {
              content?: unknown;
            };
          }
        ).message;


      if (
        typeof message?.content ===
        "string"
      ) {

        translation =
          message.content;

      } else if (
        Array.isArray(
          message?.content
        )
      ) {

        translation =
          message.content
            .map(
              (
                part
              ) => {

                if (
                  typeof part ===
                  "string"
                ) {
                  return part;
                }


                if (
                  typeof part ===
                    "object" &&
                  part !== null &&
                  "text" in part
                ) {

                  return String(
                    (
                      part as {
                        text?: unknown;
                      }
                    ).text ??
                      ""
                  );
                }


                return "";
              }
            )
            .join("");
      }
    }


    translation =
      translation
        .trim()
        .replace(
          /^["']|["']$/g,
          ""
        );


    if (!translation) {
      throw new Error(
        "Puter returned empty translation"
      );
    }


    return translation;
  }


  // ==========================================================
  // WORD TRANSLATION
  // ==========================================================

  useEffect(() => {

    const cleanWord =
      word
        .trim()
        .replace(
          /\s+/g,
          " "
        );


    if (!cleanWord) {

      setTranslatedWord(
        ""
      );

      return;
    }


    if (
      targetLanguage ===
      "en"
    ) {

      setTranslatedWord(
        cleanWord
      );

      setTranslationError(
        ""
      );

      setTranslationLoading(
        false
      );

      return;
    }


    let cancelled =
      false;


    async function run() {

      setTranslationLoading(
        true
      );

      setTranslationError(
        ""
      );


      try {

        const result =
          await translateFromEnglish(
            cleanWord
          );


        if (!cancelled) {

          setTranslatedWord(
            result
          );
        }

      } catch (error) {

        console.error(
          "Word translation:",
          error
        );


        if (!cancelled) {

          setTranslatedWord(
            cleanWord
          );

          setTranslationError(
            "Translation unavailable"
          );
        }

      } finally {

        if (!cancelled) {

          setTranslationLoading(
            false
          );
        }
      }
    }


    run();


    return () => {
      cancelled = true;
    };

  }, [
    word,
    targetLanguage,
  ]);


  // ==========================================================
  // SENTENCE TRANSLATION
  // ==========================================================

  useEffect(() => {

    const cleanSentence =
      sentence
        .join(" ")
        .trim()
        .replace(
          /\s+/g,
          " "
        );


    if (!cleanSentence) {

      setTranslatedSentence(
        ""
      );

      setSentenceTranslationError(
        ""
      );

      return;
    }


    if (
      targetLanguage ===
      "en"
    ) {

      setTranslatedSentence(
        cleanSentence
      );

      setSentenceTranslationLoading(
        false
      );

      return;
    }


    let cancelled =
      false;


    async function run() {

      setSentenceTranslationLoading(
        true
      );

      setSentenceTranslationError(
        ""
      );


      try {

        const result =
          await translateFromEnglish(
            cleanSentence
          );


        if (!cancelled) {

          setTranslatedSentence(
            result
          );
        }

      } catch (error) {

        console.error(
          "Sentence translation:",
          error
        );


        if (!cancelled) {

          setTranslatedSentence(
            cleanSentence
          );

          setSentenceTranslationError(
            "Translation unavailable"
          );
        }

      } finally {

        if (!cancelled) {

          setSentenceTranslationLoading(
            false
          );
        }
      }
    }


    run();


    return () => {
      cancelled = true;
    };

  }, [
    sentence,
    targetLanguage,
  ]);


  // ==========================================================
  // SPEECH
  // ==========================================================

  async function speakText(
    text: string
  ) {

    if (!text.trim()) {
      return;
    }


    try {

      const language =
        LANGUAGES.find(
          (item) =>
            item.code ===
            targetLanguage
        );


      const requestedLang =
        language?.speech ??
        "en-US";


      let options: any = {
        provider:
          "aws-polly",

        language:
          requestedLang,

        engine:
          "neural",
      };


      if (
        targetLanguage ===
        "ar"
      ) {

        options = {
          provider:
            "aws-polly",

          language:
            "ar-AE",

          voice:
            "Hala",

          engine:
            "neural",
        };
      }


      const audio =
        await puter.ai.txt2speech(
          text,
          options
        );


      await audio.play();

    } catch (error) {

      console.error(
        "Puter TTS error:",
        error
      );
    }
  }


  function speakWord() {
    return speakText(
      translatedWord
    );
  }


  function speakSentence() {
    return speakText(
      translatedSentence
    );
  }


  // ==========================================================
  // WEBSOCKET
  // ==========================================================

  useEffect(() => {

    mountedRef.current =
      true;

    stoppedRef.current =
      false;


    let localSocket:
      WebSocket | null = null;


    async function connect() {

      try {

        // ----------------------------------------------------
        // Check current access.
        //
        // This DOES NOT consume a trial.
        // ----------------------------------------------------

        const trial =
          await getTrialStatus();


        if (
          stoppedRef.current ||
          !mountedRef.current
        ) {
          return;
        }


        // ----------------------------------------------------
        // Anonymous user exhausted trials.
        // ----------------------------------------------------

        if (
          !trial.authenticated &&
          trial.requires_login
        ) {

          setConnected(
            false
          );

          setDetectState(
            "idle"
          );

          return;
        }


        // ----------------------------------------------------
        // Open WebSocket.
        // ----------------------------------------------------

        const wsUrl =
          getWebSocketUrl();


        console.log(
          "[EchoSign] WebSocket:",
          wsUrl
        );


        localSocket =
          new WebSocket(
            wsUrl
          );


        socketRef.current =
          localSocket;


        // ----------------------------------------------------
        // OPEN
        // ----------------------------------------------------

        localSocket.onopen =
          () => {

            if (
              stoppedRef.current
            ) {

              localSocket?.close();

              return;
            }


            console.log(
              "[EchoSign] WebSocket connected"
            );


            setConnected(
              true
            );
          };


        // ----------------------------------------------------
        // MESSAGE
        // ----------------------------------------------------

        localSocket.onmessage =
          (event) => {

            try {

              const data =
                JSON.parse(
                  event.data
                );


              console.log(
                "[EchoSign] Backend:",
                data
              );


              // RECORDING
              if (
                data.status ===
                "recording"
              ) {

                setDetectState(
                  "recording"
                );

                return;
              }


              // LANDMARKS
              if (
                data.landmarks
              ) {

                setLandmarks(
                  data.landmarks
                );
              }


              // PREDICTION
              if (
                Array.isArray(
                  data.prediction
                ) &&
                data.prediction.length > 0
              ) {

                const top =
                  data.prediction[0];


                setDetectedWord(
                  top.word
                );


                setConfidence(
                  Number(
                    top.confidence ?? 0
                  )
                );


                setCandidates(
                  data.prediction
                    .slice(1, 6)
                    .map(
                      (
                        item: any
                      ) => ({
                        word:
                          item.word,

                        conf:
                          Number(
                            item.confidence ??
                              0
                          ),
                      })
                    )
                );


                setDetectState(
                  "result"
                );


                return;
              }


              // ERROR
              if (
                data.error
              ) {

                console.error(
                  "[EchoSign] Backend error:",
                  data.error
                );


                setDetectState(
                  "idle"
                );
              }

            } catch (error) {

              console.error(
                "[EchoSign] Invalid WebSocket message:",
                error
              );
            }
          };


        // ----------------------------------------------------
        // CLOSE
        // ----------------------------------------------------

        localSocket.onclose =
          (event) => {

            console.log(
              "[EchoSign] WebSocket closed:",
              event.code,
              event.reason
            );


            setConnected(
              false
            );


            if (
              stoppedRef.current ||
              !mountedRef.current
            ) {
              return;
            }


            if (
              requiresLoginRef.current
            ) {
              return;
            }


            if (
              reconnectTimerRef.current
            ) {

              window.clearTimeout(
                reconnectTimerRef.current
              );
            }


            reconnectTimerRef.current =
              window.setTimeout(
                () => {
                  connect();
                },
                3000
              );
          };


        // ----------------------------------------------------
        // ERROR
        // ----------------------------------------------------

        localSocket.onerror =
          (error) => {

            console.error(
              "[EchoSign] WebSocket error:",
              error
            );


            setConnected(
              false
            );
          };

      } catch (error) {

        console.error(
          "[EchoSign] Connection failed:",
          error
        );


        setConnected(
          false
        );


        if (
          stoppedRef.current ||
          !mountedRef.current
        ) {
          return;
        }


        reconnectTimerRef.current =
          window.setTimeout(
            () => {
              connect();
            },
            3000
          );
      }
    }


    connect();


    // CLEANUP
    return () => {

      stoppedRef.current =
        true;

      mountedRef.current =
        false;


      if (
        reconnectTimerRef.current
      ) {

        window.clearTimeout(
          reconnectTimerRef.current
        );

        reconnectTimerRef.current =
          null;
      }


      if (localSocket) {

        localSocket.onclose =
          null;

        localSocket.onerror =
          null;

        localSocket.onmessage =
          null;

        localSocket.close();
      }


      if (
        socketRef.current
      ) {

        socketRef.current.close();

        socketRef.current =
          null;
      }
    };

  }, []);


  // ==========================================================
  // CAMERA FRAME SENDER
  // ==========================================================

  useEffect(() => {

    const timer =
      window.setInterval(
        async () => {

          if (
            detectStateRef.current !==
            "recording"
          ) {
            return;
          }


          if (
            !webcamRef.current
          ) {
            return;
          }


          const socket =
            socketRef.current;


          if (
            !socket ||
            socket.readyState !==
              WebSocket.OPEN
          ) {
            return;
          }


          try {

            const screenshot =
              webcamRef.current
                .getScreenshot();


            if (!screenshot) {
              return;
            }


            const response =
              await fetch(
                screenshot
              );


            const blob =
              await response.blob();


            if (
              socket.readyState ===
              WebSocket.OPEN
            ) {

              socket.send(
                blob
              );
            }

          } catch (error) {

            console.error(
              "[EchoSign] Camera frame error:",
              error
            );
          }

        },
        100
      );


    return () => {

      window.clearInterval(
        timer
      );
    };

  }, []);


  // ==========================================================
  // START RECORDING
  // ==========================================================

  function startRecording() {

    // Anonymous user has no trials left.
    if (
      !authenticatedRef.current &&
      requiresLoginRef.current
    ) {

      return;
    }


    // Extra safety check.
    if (
      !authenticatedRef.current &&
      trialsRemaining !== null &&
      trialsRemaining <= 0
    ) {

      updateRequiresLogin(
        true
      );

      return;
    }


    const socket =
      socketRef.current;


    if (
      !socket ||
      socket.readyState !==
        WebSocket.OPEN
    ) {

      console.log(
        "[EchoSign] WebSocket not ready"
      );

      return;
    }


    socket.send(
      JSON.stringify({
        action: "start",
      })
    );


    setDetectedWord(
      "Recording..."
    );


    setConfidence(
      0
    );


    setCandidates(
      []
    );


    setLandmarks(
      null
    );


    setDetectState(
      "recording"
    );
  }


  // ==========================================================
  // STOP RECORDING
  // ==========================================================

  function stopRecording() {

    const socket =
      socketRef.current;


    if (
      !socket ||
      socket.readyState !==
        WebSocket.OPEN
    ) {

      console.log(
        "[EchoSign] WebSocket not ready"
      );

      return;
    }


    socket.send(
      JSON.stringify({
        action: "stop",
      })
    );
  }


  // ==========================================================
  // CONFIRM
  //
  // THIS IS WHERE THE TRIAL IS CONSUMED.
  // ==========================================================

  async function confirmSign() {

    if (
      !word ||
      word === "Waiting..." ||
      word === "Recording..."
    ) {

      return;
    }


    // --------------------------------------------------------
    // Prevent duplicate requests.
    // --------------------------------------------------------

    if (
      consumingTrialRef.current
    ) {

      return;
    }


    // --------------------------------------------------------
    // Authenticated users are unlimited.
    // --------------------------------------------------------

    if (
      authenticatedRef.current
    ) {

      setSentence(
        previous => [
          ...previous,
          word,
        ]
      );


      setDetectState(
        "confirmed"
      );


      return;
    }


    // --------------------------------------------------------
    // Anonymous users must have a trial.
    // --------------------------------------------------------

    if (
      requiresLoginRef.current ||
      (
        trialsRemaining !== null &&
        trialsRemaining <= 0
      )
    ) {

      updateRequiresLogin(
        true
      );

      setTrialsRemaining(
        0
      );

      setDetectState(
        "idle"
      );

      return;
    }


    // --------------------------------------------------------
    // Consume ONE trial.
    // --------------------------------------------------------

    consumingTrialRef.current =
      true;


    try {

      console.log(
        "[EchoSign] Consuming anonymous trial..."
      );


      const result =
        await consumeAnonymousTrial();


      console.log(
        "[EchoSign] Trial consumed:",
        result
      );


      // ------------------------------------------------------
      // Backend says trials are exhausted.
      // ------------------------------------------------------

      if (
        result.requires_login ||
        (
          typeof result.trials_remaining ===
            "number" &&
          result.trials_remaining <= 0
        )
      ) {

        setTrialsRemaining(
          0
        );

        updateRequiresLogin(
          true
        );

        setDetectState(
          "idle"
        );

        return;
      }


      // ------------------------------------------------------
      // Successfully consumed.
      // Add word to sentence.
      // ------------------------------------------------------

      setSentence(
        previous => [
          ...previous,
          word,
        ]
      );


      setDetectState(
        "confirmed"
      );

    } catch (error) {

      console.error(
        "[EchoSign] Failed to consume trial:",
        error
      );


      // Do not confirm the word if the
      // backend did not accept the trial.

      setDetectState(
        "idle"
      );

    } finally {

      consumingTrialRef.current =
        false;
    }
  }


  // ==========================================================
  // RESET
  // ==========================================================

  function reset() {

    setConfidence(
      0
    );


    setCandidates(
      []
    );


    setLandmarks(
      null
    );


    setTranslatedWord(
      ""
    );


    setTranslationError(
      ""
    );


    setDetectedWord(
      "Waiting..."
    );


    setDetectState(
      "idle"
    );
  }


  // ==========================================================
  // NEW SENTENCE
  // ==========================================================

  function newSentence() {

    setSentence(
      []
    );


    setTranslatedSentence(
      ""
    );


    setSentenceTranslationError(
      ""
    );
  }


  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div
      className="
        flex-1
        px-6
        py-8
        flex
        flex-col
        gap-6
      "
    >

      {/* ================================================== */}
      {/* TOP STATUS */}
      {/* ================================================== */}

      <div
        className="
          flex
          items-center
          justify-between
          gap-4
          flex-wrap
        "
      >

        <div
          className="
            flex
            items-center
            gap-3
            flex-wrap
          "
        >

          {/* AUTHENTICATED */}

          {authenticated && (

            <div
              className="
                rounded-full
                bg-purple-50
                text-purple-700
                px-3
                py-1.5
                text-sm
                font-semibold
              "
            >
              Signed in · Unlimited
            </div>

          )}


          {/* ANONYMOUS TRIALS */}

          {!authenticated &&
            trialsRemaining !== null && (

            <div
              className="
                rounded-full
                bg-purple-50
                text-purple-700
                px-3
                py-1.5
                text-sm
                font-semibold
              "
            >

              {trialsRemaining}{" "}
              trial
              {trialsRemaining !== 1
                ? "s"
                : ""}{" "}
              remaining

            </div>

          )}

        </div>

      </div>


      {/* ================================================== */}
      {/* LOGIN REQUIRED */}
      {/* ================================================== */}

      {requiresLogin &&
        !authenticated && (

        <motion.div
          initial={{
            opacity: 0,
            y: -10,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          className="
            rounded-2xl
            border
            border-orange-200
            bg-orange-50
            p-5
          "
        >

          <p
            className="
              font-bold
              text-orange-700
            "
          >
            Free trials finished
          </p>


          <p
            className="
              mt-1
              text-sm
              text-orange-600
            "
          >
            Please log in to continue
            using EchoSign.
          </p>

        </motion.div>

      )}


      {/* ================================================== */}
      {/* INSTRUCTION */}
      {/* ================================================== */}

      <AnimatePresence>

        {detectState === "idle" && (

          <motion.div
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
            className="
              rounded-2xl
              p-5
              bg-white
              border
            "
          >

            <div
              className="
                flex
                items-center
                gap-3
              "
            >

              <Hand
                size={20}
                color="#6C47FF"
              />


              <p>

                Press{" "}
                <b>Record</b>,
                perform the sign,
                then press{" "}
                <b>Stop</b>.

              </p>

            </div>

          </motion.div>

        )}

      </AnimatePresence>


      {/* ================================================== */}
      {/* CAMERA + RESULT */}
      {/* ================================================== */}

      <div
        className="
          grid
          gap-6
        "
        style={{
          gridTemplateColumns:
            "minmax(0, 1.1fr) minmax(0, .9fr)",
        }}
      >

        {/* CAMERA */}

        <div
          className="
            rounded-3xl
            overflow-hidden
            relative
          "
          style={{
            aspectRatio: "4/3",
            background: "#111",
          }}
        >

          <Webcam
            ref={webcamRef}
            audio={false}
            screenshotFormat="image/jpeg"
            screenshotQuality={0.8}
            videoConstraints={{
              facingMode: "user",
              width: 1280,
              height: 720,
            }}
            className="
              w-full
              h-full
              object-cover
            "
          />


          <div
            className="
              absolute
              inset-0
              pointer-events-none
            "
          >

            <CameraOverlay
              landmarks={landmarks}
              confidence={confidence}
            />

          </div>


          {/* CAMERA STATUS */}

          <div
            className="
              absolute
              top-4
              left-4
              right-4
              flex
              justify-between
              items-center
            "
          >

            <div
              className="
                rounded-full
                bg-black/60
                text-white
                px-3
                py-1.5
                text-xs
                font-semibold
                backdrop-blur
              "
            >

              {detectState === "recording"
                ? "● Recording"
                : "Camera ready"}

            </div>


            {landmarks && (

              <div
                className="
                  rounded-full
                  bg-green-500/80
                  text-white
                  px-3
                  py-1.5
                  text-xs
                  font-semibold
                "
              >
                Hands detected
              </div>

            )}

          </div>


          {/* CAMERA BUTTONS */}

          <div
            className="
              absolute
              bottom-5
              left-0
              right-0
              flex
              justify-center
              gap-3
            "
          >

            {/* RECORD */}

            {detectState === "idle" && (

              <button
                onClick={startRecording}
                disabled={
                  !connected ||
                  (
                    !authenticated &&
                    (
                      requiresLogin ||
                      (
                        trialsRemaining !== null &&
                        trialsRemaining <= 0
                      )
                    )
                  )
                }
                className="
                  flex
                  items-center
                  gap-2
                  bg-purple-600
                  text-white
                  rounded-xl
                  px-8
                  py-3
                  font-semibold
                  shadow-lg
                  hover:bg-purple-700
                  disabled:opacity-40
                  disabled:cursor-not-allowed
                  transition
                "
              >

                <Circle
                  size={17}
                />

                Record Sign

              </button>

            )}


            {/* STOP */}

            {detectState ===
              "recording" && (

              <button
                onClick={stopRecording}
                className="
                  bg-red-500
                  text-white
                  rounded-xl
                  px-8
                  py-3
                  font-semibold
                  shadow-lg
                  hover:bg-red-600
                "
              >
                Stop Recording
              </button>

            )}


            {/* RESULT */}

            {detectState ===
              "result" && (

              <div
                className="
                  bg-white/90
                  text-purple-700
                  rounded-xl
                  px-6
                  py-3
                  font-semibold
                  backdrop-blur
                "
              >
                Processing complete
              </div>

            )}

          </div>

        </div>


        {/* ================================================= */}
        {/* RESULT PANEL */}
        {/* ================================================= */}

        <div
          className="
            rounded-3xl
            bg-white
            border
            p-7
            flex
            flex-col
            gap-5
            min-h-[420px]
          "
        >

          {/* IDLE */}

          {detectState === "idle" && (

            <div
              className="
                flex
                flex-col
                items-center
                justify-center
                h-full
                text-center
              "
            >

              <h2
                className="
                  text-2xl
                  font-black
                  text-gray-800
                "
              >
                Ready
              </h2>


              <p
                className="
                  text-gray-500
                  mt-3
                "
              >
                Press Record and
                make your sign.
              </p>

            </div>

          )}


          {/* RECORDING */}

          {detectState ===
            "recording" && (

            <div
              className="
                flex
                flex-col
                items-center
                justify-center
                h-full
                text-center
              "
            >

              <div
                className="
                  text-red-500
                  text-xl
                  font-black
                "
              >
                ● Recording
              </div>


              <p
                className="
                  mt-3
                  text-gray-500
                "
              >
                Perform your sign
                then press Stop.
              </p>


              <div
                className="
                  mt-6
                  w-12
                  h-12
                  rounded-full
                  border-4
                  border-purple-200
                  border-t-purple-600
                  animate-spin
                "
              />

            </div>

          )}


          {/* RESULT */}

          {detectState ===
            "result" && (

            <>

              <p
                className="
                  text-xs
                  font-bold
                  tracking-wide
                  text-purple-300
                "
              >
                WE THINK YOU SIGNED
              </p>


              <div
                className="
                  flex
                  items-center
                  justify-between
                  gap-4
                  flex-wrap
                "
              >

                <h1
                  className="
                    text-5xl
                    lg:text-6xl
                    font-black
                    text-gray-900
                  "
                >
                  {word}
                </h1>


                <div
                  className="
                    flex
                    items-center
                    gap-2
                  "
                >

                  <select
                    value={
                      targetLanguage
                    }
                    onChange={
                      event =>
                        setTargetLanguage(
                          event.target.value
                        )
                    }
                    className="
                      border
                      border-gray-200
                      bg-gray-50
                      rounded-xl
                      px-3
                      py-2
                      text-sm
                      font-semibold
                      text-gray-700
                      outline-none
                    "
                  >

                    {LANGUAGES.map(
                      language => (

                        <option
                          key={
                            language.code
                          }
                          value={
                            language.code
                          }
                        >
                          {
                            language.name
                          }
                        </option>

                      )
                    )}

                  </select>


                  <button
                    type="button"
                    onClick={speakWord}
                    disabled={
                      translationLoading ||
                      !translatedWord
                    }
                    className="
                      w-11
                      h-11
                      rounded-xl
                      bg-purple-600
                      text-white
                      flex
                      items-center
                      justify-center
                      hover:scale-105
                      disabled:opacity-40
                      transition
                    "
                  >

                    <Volume2
                      size={19}
                    />

                  </button>

                </div>

              </div>


              {/* TRANSLATION */}

              <div
                className="
                  rounded-2xl
                  bg-purple-50
                  border
                  border-purple-100
                  px-4
                  py-3
                "
              >

                <div
                  className="
                    flex
                    items-center
                    justify-between
                    gap-3
                  "
                >

                  <div>

                    <p
                      className="
                        text-xs
                        font-bold
                        text-purple-400
                        uppercase
                        tracking-wide
                        mb-1
                      "
                    >
                      {
                        LANGUAGES.find(
                          l =>
                            l.code ===
                            targetLanguage
                        )?.name
                      }
                    </p>


                    <p
                      className="
                        text-2xl
                        font-black
                        text-purple-700
                      "
                    >

                      {translationLoading
                        ? "Translating..."
                        : translatedWord}

                    </p>

                  </div>


                  {!translationLoading &&
                    translatedWord && (

                    <button
                      type="button"
                      onClick={speakWord}
                      className="
                        p-2
                        rounded-lg
                        text-purple-600
                        hover:bg-purple-100
                      "
                    >

                      <Volume2
                        size={18}
                      />

                    </button>

                  )}

                </div>


                {translationError && (

                  <p
                    className="
                      text-xs
                      text-orange-500
                      mt-2
                    "
                  >
                    {translationError}
                  </p>

                )}

              </div>


              {/* CONFIDENCE */}

              <div>

                <div
                  className="
                    flex
                    items-center
                    justify-between
                    mb-2
                  "
                >

                  <p
                    className="
                      text-sm
                      font-semibold
                    "
                  >
                    Confidence
                  </p>


                  <p
                    className="
                      font-bold
                      text-purple-600
                    "
                  >
                    {animConf.toFixed(0)}%
                  </p>

                </div>


                <div
                  className="
                    w-full
                    h-3
                    bg-gray-200
                    rounded-full
                    overflow-hidden
                  "
                >

                  <div
                    className="
                      h-full
                      bg-purple-600
                      rounded-full
                      transition-all
                    "
                    style={{
                      width:
                        `${Math.min(
                          100,
                          Math.max(
                            0,
                            animConf
                          )
                        )}%`,
                    }}
                  />

                </div>

              </div>


              {/* TOP FIVE */}

              <TopFiveList
                topWord={word}
                topConf={confidence}
                candidates={candidates}
              />


              {/* CONFIRM / REJECT */}

              <div
                className="
                  flex
                  gap-3
                "
              >

                <button
                  onClick={confirmSign}
                  disabled={
                    consumingTrialRef.current
                  }
                  className="
                    flex-1
                    bg-purple-600
                    text-white
                    rounded-xl
                    p-3
                    flex
                    items-center
                    justify-center
                    gap-2
                    hover:bg-purple-700
                    disabled:opacity-50
                    disabled:cursor-not-allowed
                  "
                >

                  <CheckCircle
                    size={17}
                  />

                  Yes

                </button>


                <button
                  onClick={reset}
                  disabled={
                    consumingTrialRef.current
                  }
                  className="
                    flex-1
                    border
                    rounded-xl
                    p-3
                    flex
                    items-center
                    justify-center
                    gap-2
                    hover:bg-gray-50
                    disabled:opacity-50
                  "
                >

                  <XCircle
                    size={17}
                  />

                  No

                </button>

              </div>

            </>

          )}


          {/* CONFIRMED */}

          {detectState ===
            "confirmed" && (

            <div
              className="
                flex
                flex-col
                items-center
                justify-center
                text-center
                gap-5
                h-full
              "
            >

              <div
                className="
                  w-20
                  h-20
                  rounded-full
                  bg-purple-600
                  flex
                  items-center
                  justify-center
                "
              >

                <Check
                  size={40}
                  color="white"
                />

              </div>


              <h2
                className="
                  text-3xl
                  font-black
                "
              >
                Confirmed
              </h2>


              <p
                className="
                  text-gray-500
                "
              >
                You signed:
              </p>


              <h1
                className="
                  text-5xl
                  font-black
                "
              >
                {word}
              </h1>


              {translatedWord && (

                <div
                  className="
                    flex
                    items-center
                    gap-2
                    text-purple-600
                  "
                >

                  <span
                    className="
                      text-xl
                      font-bold
                    "
                  >
                    {translatedWord}
                  </span>


                  <button
                    type="button"
                    onClick={speakWord}
                    className="
                      p-2
                      rounded-lg
                      hover:bg-purple-50
                    "
                  >

                    <Volume2
                      size={19}
                    />

                  </button>

                </div>

              )}


              <button
                onClick={reset}
                className="
                  bg-purple-600
                  text-white
                  rounded-xl
                  px-8
                  py-3
                  font-semibold
                  hover:bg-purple-700
                "
              >
                Sign another word
              </button>

            </div>

          )}

        </div>

      </div>


      {/* ================================================== */}
      {/* SENTENCE */}
      {/* ================================================== */}

      <div
        className="
          rounded-3xl
          bg-white
          border
          p-6
          flex
          flex-col
          gap-4
        "
      >

        <div
          className="
            flex
            items-center
            justify-between
            gap-3
          "
        >

          <p
            className="
              text-xs
              font-bold
              tracking-wide
              text-purple-300
            "
          >
            SENTENCE
          </p>


          <button
            onClick={newSentence}
            disabled={
              sentence.length === 0
            }
            className="
              flex
              items-center
              gap-2
              text-sm
              font-semibold
              text-purple-600
              border
              border-purple-200
              rounded-lg
              px-3
              py-1.5
              hover:bg-purple-50
              disabled:opacity-40
            "
          >

            <RotateCcw
              size={14}
            />

            New Sentence

          </button>

        </div>


        <div
          className="
            flex
            items-center
            justify-between
            gap-3
          "
        >

          <p
            className="
              text-2xl
              font-black
              text-gray-900
              min-h-[2.5rem]
            "
          >

            {sentence.length > 0 ? (

              sentence.join(" ")

            ) : (

              <span
                className="
                  text-gray-300
                  font-semibold
                "
              >
                Confirmed words
                will appear here...
              </span>

            )}

          </p>


          <button
            type="button"
            onClick={speakSentence}
            disabled={
              sentenceTranslationLoading ||
              !translatedSentence
            }
            className="
              p-2
              rounded-lg
              text-purple-600
              hover:bg-purple-100
              disabled:opacity-40
            "
          >

            <Volume2
              size={18}
            />

          </button>

        </div>


        {/* SENTENCE TRANSLATION */}

        {(translatedSentence ||
          sentenceTranslationLoading) && (

          <div
            className="
              rounded-2xl
              bg-gray-50
              border
              border-gray-100
              px-4
              py-3
            "
          >

            <div
              className="
                flex
                items-center
                justify-between
                gap-3
              "
            >

              <div>

                <p
                  className="
                    text-xs
                    font-bold
                    text-gray-400
                    uppercase
                    tracking-wide
                    mb-1
                  "
                >
                  {
                    LANGUAGES.find(
                      l =>
                        l.code ===
                        targetLanguage
                    )?.name
                  }{" "}
                  Sentence
                </p>


                <p
                  className="
                    text-base
                    font-bold
                    text-gray-700
                  "
                >

                  {sentenceTranslationLoading
                    ? "Translating..."
                    : translatedSentence}

                </p>

              </div>


              {!sentenceTranslationLoading &&
                translatedSentence && (

                <button
                  type="button"
                  onClick={speakSentence}
                  className="
                    p-2
                    rounded-lg
                    text-purple-600
                    hover:bg-purple-100
                  "
                >

                  <Volume2
                    size={18}
                  />

                </button>

              )}

            </div>


            {sentenceTranslationError && (

              <p
                className="
                  text-xs
                  text-orange-500
                  mt-2
                "
              >
                {sentenceTranslationError}
              </p>

            )}

          </div>

        )}

      </div>

    </div>
  );
}

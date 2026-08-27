import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { Check, X, Loader2, ArrowRight } from "lucide-react";
import { motion } from "motion/react";
import axios from "axios";


export default function VerifyEmailPage() {

  const [searchParams] = useSearchParams();

  const navigate = useNavigate();

  const [status, setStatus] = useState<
    "loading" | "success" | "error"
  >("loading");

  const [message, setMessage] = useState("");


  useEffect(() => {

    const token = searchParams.get("token");

    if (!token) {

      setStatus("error");

      setMessage(
        "No verification token was provided."
      );

      return;
    }


    const verifyEmail = async () => {

      try {

        const response = await axios.get(
          "http://localhost:8000/auth/verify-email",
          {
            params: {
              token
            }
          }
        );

        setStatus("success");

        setMessage(response.data.message);

      } catch (error: any) {

        setStatus("error");

        setMessage(
          error.response?.data?.detail ||
          "Verification failed."
        );
      }
    };


    verifyEmail();

  }, [searchParams]);


  return (

    <div
      className="min-h-screen flex items-center
                 justify-center px-4"
      style={{
        background: "#F8F7FF",
        fontFamily: "Inter, sans-serif"
      }}
    >

      <motion.div
        initial={{
          opacity: 0,
          scale: 0.95
        }}
        animate={{
          opacity: 1,
          scale: 1
        }}
        className="rounded-3xl p-10
                   text-center shadow-sm
                   max-w-md w-full"
        style={{
          background: "#FFFFFF",
          border: "1px solid #E2E0F8"
        }}
      >

        {status === "loading" && (

          <>
            <Loader2
              size={50}
              className="mx-auto mb-6 animate-spin"
              style={{
                color: "#6C47FF"
              }}
            />

            <h1
              className="font-black text-3xl mb-3"
              style={{
                color: "#1A1535",
                fontFamily: "Nunito, sans-serif"
              }}
            >
              Verifying your email...
            </h1>

            <p
              style={{
                color: "#7B7BA0"
              }}
            >
              Please wait a moment.
            </p>
          </>

        )}


        {status === "success" && (

          <>
            <div
              className="mx-auto mb-6
                         flex items-center
                         justify-center
                         rounded-full"
              style={{
                width: 80,
                height: 80,
                background:
                  "linear-gradient(135deg, #6C47FF, #9D7BFF)"
              }}
            >
              <Check
                size={40}
                color="white"
                strokeWidth={3}
              />
            </div>


            <h1
              className="font-black text-3xl mb-3"
              style={{
                color: "#1A1535",
                fontFamily: "Nunito, sans-serif"
              }}
            >
              Email verified!
            </h1>


            <p
              className="mb-8"
              style={{
                color: "#7B7BA0"
              }}
            >
              Your account has been verified
              successfully. You can now sign in.
            </p>


            <button
              onClick={() => navigate("/signin")}
              className="flex items-center
                         justify-center gap-2
                         w-full py-4 rounded-2xl
                         font-bold"
              style={{
                background:
                  "linear-gradient(135deg, #6C47FF, #9D7BFF)",
                color: "white"
              }}
            >
              Sign in
              <ArrowRight size={18} />
            </button>
          </>

        )}


        {status === "error" && (

          <>
            <div
              className="mx-auto mb-6
                         flex items-center
                         justify-center
                         rounded-full"
              style={{
                width: 80,
                height: 80,
                background: "#FEE2E2"
              }}
            >
              <X
                size={40}
                color="#EF4444"
                strokeWidth={3}
              />
            </div>


            <h1
              className="font-black text-3xl mb-3"
              style={{
                color: "#1A1535",
                fontFamily: "Nunito, sans-serif"
              }}
            >
              Verification failed
            </h1>


            <p
              className="mb-8"
              style={{
                color: "#7B7BA0"
              }}
            >
              {message}
            </p>


            <button
              onClick={() => navigate("/signin")}
              className="flex items-center
                         justify-center gap-2
                         w-full py-4 rounded-2xl
                         font-bold"
              style={{
                background: "#6C47FF",
                color: "white"
              }}
            >
              Go to sign in
            </button>
          </>

        )}

      </motion.div>

    </div>
  );
}
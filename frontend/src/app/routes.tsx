import { createBrowserRouter } from "react-router";
import Root from "./Root";
import HomePage from "./pages/HomePage";
import TranslatePage from "./pages/TranslatePage";
import AboutPage from "./pages/AboutPage";
import SignUpPage from "./pages/SignUpPage";
import SignInPage from "./pages/SignInPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: AboutPage  },
      { path: "translate", Component: TranslatePage },
      { path: "Detect", Component:  HomePage},
      { path: "signup", Component: SignUpPage },
      { path: "signin", Component: SignInPage },
      {
        path: "verify-email",
        Component: VerifyEmailPage
      },
      {
        path: "forgot-password",
        Component: ForgotPasswordPage
      },
      {
        path: "reset-password",
        Component: ResetPasswordPage
      },
      
      
    ],
  },
]);

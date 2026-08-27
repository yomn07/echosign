import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_verification_email(
    recipient_email: str,
    first_name: str,
    verification_link: str
):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")

    message = EmailMessage()

    message["Subject"] = "Verify your EchoSign account"
    message["From"] = smtp_from
    message["To"] = recipient_email

    # Plain-text fallback
    message.set_content(
        f"""
Hello {first_name},

Welcome to EchoSign!

We're excited to have you with us. Please verify your email address by clicking the link below:

{verification_link}

This verification link will expire in 30 minutes.

If you didn't create an EchoSign account, you can safely ignore this email.

Best regards,
The EchoSign Team
""".strip()
    )

    # HTML version
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify your EchoSign account</title>
</head>

<body style="
    margin: 0;
    padding: 0;
    background-color: #f4f6f8;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 Helvetica, Arial, sans-serif;
    color: #1f2937;
">

    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background-color: #f4f6f8; padding: 40px 20px;">

        <tr>
            <td align="center">

                <!-- Main container -->
                <table width="100%" cellpadding="0" cellspacing="0" border="0"
                       style="
                           max-width: 600px;
                           background-color: #ffffff;
                           border-radius: 16px;
                           overflow: hidden;
                           box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
                       ">

                    <!-- Header -->
                    <tr>
                        <td align="center"
                            style="
                                padding: 32px 40px;
                                background-color: #111827;
                            ">

                            <div style="
                                font-size: 28px;
                                font-weight: 700;
                                letter-spacing: -0.5px;
                                color: #ffffff;
                            ">
                                Echo<span style="color: #6366f1;">Sign</span>
                            </div>

                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 45px 45px 35px 45px;">

                            <h1 style="
                                margin: 0 0 18px 0;
                                font-size: 28px;
                                line-height: 1.3;
                                font-weight: 700;
                                color: #111827;
                            ">
                                Welcome to EchoSign, {first_name}! 👋
                            </h1>

                            <p style="
                                margin: 0 0 18px 0;
                                font-size: 16px;
                                line-height: 1.7;
                                color: #4b5563;
                            ">
                                Thanks for creating your EchoSign account.
                                We're excited to have you here.
                            </p>

                            <p style="
                                margin: 0 0 30px 0;
                                font-size: 16px;
                                line-height: 1.7;
                                color: #4b5563;
                            ">
                                To get started, please verify your email address
                                by clicking the button below.
                            </p>

                            <!-- Button -->
                            <table cellpadding="0" cellspacing="0" border="0"
                                   width="100%">
                                <tr>
                                    <td align="center">

                                        <a href="{verification_link}"
                                           style="
                                               display: inline-block;
                                               padding: 15px 30px;
                                               background-color: #6366f1;
                                               color: #ffffff;
                                               text-decoration: none;
                                               font-size: 16px;
                                               font-weight: 600;
                                               border-radius: 10px;
                                               line-height: 1.2;
                                           ">
                                            Verify My Email
                                        </a>

                                    </td>
                                </tr>
                            </table>

                            <!-- Expiration notice -->
                            <table width="100%" cellpadding="0" cellspacing="0"
                                   border="0"
                                   style="
                                       margin-top: 32px;
                                       background-color: #f9fafb;
                                       border-radius: 10px;
                                   ">
                                <tr>
                                    <td style="
                                        padding: 16px 18px;
                                        font-size: 14px;
                                        line-height: 1.6;
                                        color: #6b7280;
                                    ">

                                        <strong style="color: #374151;">
                                            ⏱ This link expires in 30 minutes.
                                        </strong>
                                        <br>
                                        For your security, please verify your
                                        email before the link expires.

                                    </td>
                                </tr>
                            </table>

                            <!-- Fallback link -->
                            <p style="
                                margin: 30px 0 8px 0;
                                font-size: 13px;
                                line-height: 1.6;
                                color: #9ca3af;
                            ">
                                If the button doesn't work, copy and paste this
                                link into your browser:
                            </p>

                            <p style="
                                margin: 0;
                                font-size: 13px;
                                line-height: 1.6;
                                word-break: break-all;
                            ">
                                <a href="{verification_link}"
                                   style="
                                       color: #6366f1;
                                       text-decoration: none;
                                   ">
                                    {verification_link}
                                </a>
                            </p>

                        </td>
                    </tr>

                    <!-- Security note -->
                    <tr>
                        <td style="
                            padding: 0 45px 35px 45px;
                        ">

                            <div style="
                                height: 1px;
                                background-color: #e5e7eb;
                            "></div>

                            <p style="
                                margin: 25px 0 0 0;
                                font-size: 13px;
                                line-height: 1.6;
                                color: #9ca3af;
                            ">
                                If you didn't create an EchoSign account,
                                you can safely ignore this email. No action
                                is required.
                            </p>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td align="center"
                            style="
                                padding: 25px 40px;
                                background-color: #f9fafb;
                                border-top: 1px solid #f3f4f6;
                            ">

                            <p style="
                                margin: 0;
                                font-size: 13px;
                                color: #9ca3af;
                            ">
                                © EchoSign · All rights reserved
                            </p>

                        </td>
                    </tr>

                </table>

                <!-- Footer outside card -->
                <p style="
                    max-width: 500px;
                    margin: 20px auto 0 auto;
                    font-size: 12px;
                    line-height: 1.5;
                    color: #9ca3af;
                ">
                    This is an automated message. Please do not reply directly
                    to this email.
                </p>

            </td>
        </tr>

    </table>

</body>
</html>
"""

    message.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()

        server.login(
            smtp_username,
            smtp_password
        )

        server.send_message(message)



def send_password_reset_email(
    recipient_email: str,
    first_name: str,
    reset_link: str
):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")

    message = EmailMessage()

    message["Subject"] = "Reset your EchoSign password"
    message["From"] = smtp_from
    message["To"] = recipient_email

    # Plain-text fallback
    message.set_content(
        f"""
Hello {first_name},

We received a request to reset your EchoSign password.

Click the link below to create a new password:

{reset_link}

This password reset link will expire in 30 minutes.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The EchoSign Team
""".strip()
    )

    # HTML version
    html_content = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>Reset your EchoSign password</title>
</head>

<body style="
    margin: 0;
    padding: 0;
    background-color: #f4f6f8;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 Helvetica, Arial, sans-serif;
    color: #1f2937;
">

    <table
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="
            background-color: #f4f6f8;
            padding: 40px 20px;
        "
    >
        <tr>
            <td align="center">

                <!-- Main container -->
                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    style="
                        max-width: 600px;
                        background-color: #ffffff;
                        border-radius: 16px;
                        overflow: hidden;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
                    "
                >

                    <!-- Header -->
                    <tr>
                        <td
                            align="center"
                            style="
                                padding: 32px 40px;
                                background-color: #111827;
                            "
                        >
                            <div style="
                                font-size: 28px;
                                font-weight: 700;
                                letter-spacing: -0.5px;
                                color: #ffffff;
                            ">
                                Echo<span style="color: #6366f1;">
                                    Sign
                                </span>
                            </div>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 45px 45px 35px 45px;">

                            <h1 style="
                                margin: 0 0 18px 0;
                                font-size: 28px;
                                line-height: 1.3;
                                font-weight: 700;
                                color: #111827;
                            ">
                                Reset your password 🔐
                            </h1>

                            <p style="
                                margin: 0 0 18px 0;
                                font-size: 16px;
                                line-height: 1.7;
                                color: #4b5563;
                            ">
                                Hi {first_name},
                            </p>

                            <p style="
                                margin: 0 0 30px 0;
                                font-size: 16px;
                                line-height: 1.7;
                                color: #4b5563;
                            ">
                                We received a request to reset your
                                EchoSign password. Click the button below
                                to create a new password.
                            </p>

                            <!-- Button -->
                            <table
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                width="100%"
                            >
                                <tr>
                                    <td align="center">

                                        <a
                                            href="{reset_link}"
                                            style="
                                                display: inline-block;
                                                padding: 15px 30px;
                                                background-color: #6366f1;
                                                color: #ffffff;
                                                text-decoration: none;
                                                font-size: 16px;
                                                font-weight: 600;
                                                border-radius: 10px;
                                                line-height: 1.2;
                                            "
                                        >
                                            Reset My Password
                                        </a>

                                    </td>
                                </tr>
                            </table>

                            <!-- Expiration notice -->
                            <table
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    margin-top: 32px;
                                    background-color: #f9fafb;
                                    border-radius: 10px;
                                "
                            >
                                <tr>
                                    <td style="
                                        padding: 16px 18px;
                                        font-size: 14px;
                                        line-height: 1.6;
                                        color: #6b7280;
                                    ">

                                        <strong style="color: #374151;">
                                            ⏱ This link expires in 30 minutes.
                                        </strong>

                                        <br>

                                        For your security, this password
                                        reset link can only be used once.

                                    </td>
                                </tr>
                            </table>

                            <!-- Fallback link -->
                            <p style="
                                margin: 30px 0 8px 0;
                                font-size: 13px;
                                line-height: 1.6;
                                color: #9ca3af;
                            ">
                                If the button doesn't work, copy and paste
                                this link into your browser:
                            </p>

                            <p style="
                                margin: 0;
                                font-size: 13px;
                                line-height: 1.6;
                                word-break: break-all;
                            ">
                                <a
                                    href="{reset_link}"
                                    style="
                                        color: #6366f1;
                                        text-decoration: none;
                                    "
                                >
                                    {reset_link}
                                </a>
                            </p>

                        </td>
                    </tr>

                    <!-- Security note -->
                    <tr>
                        <td style="padding: 0 45px 35px 45px;">

                            <div style="
                                height: 1px;
                                background-color: #e5e7eb;
                            "></div>

                            <p style="
                                margin: 25px 0 0 0;
                                font-size: 13px;
                                line-height: 1.6;
                                color: #9ca3af;
                            ">
                                If you didn't request a password reset,
                                you can safely ignore this email. Your
                                password will remain unchanged.
                            </p>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td
                            align="center"
                            style="
                                padding: 25px 40px;
                                background-color: #f9fafb;
                                border-top: 1px solid #f3f4f6;
                            "
                        >
                            <p style="
                                margin: 0;
                                font-size: 13px;
                                color: #9ca3af;
                            ">
                                © EchoSign · All rights reserved
                            </p>
                        </td>
                    </tr>

                </table>

                <!-- Footer outside card -->
                <p style="
                    max-width: 500px;
                    margin: 20px auto 0 auto;
                    font-size: 12px;
                    line-height: 1.5;
                    color: #9ca3af;
                ">
                    This is an automated message. Please do not reply
                    directly to this email.
                </p>

            </td>
        </tr>
    </table>

</body>
</html>
"""

    message.add_alternative(
        html_content,
        subtype="html"
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as server:

        server.starttls()

        server.login(
            smtp_username,
            smtp_password
        )

        server.send_message(message)

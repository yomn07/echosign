# EchoSign Authentication Service

## 1. Purpose

The Auth Service manages users and authentication.

Responsibilities include:

* Registration.
* Login.
* Logout.
* User validation.
* Authentication tokens.
* Email verification.
* Forgot password.
* Password reset.
* Authentication security.

---

## 2. Docker

Internal address:

```text
auth-service:8001
```

The frontend should access it through the gateway.

---

## 3. Registration

Typical flow:

```text
Register
   ↓
POST /api/auth/register
   ↓
Auth Service
   ↓
Create user
   ↓
Hash password
   ↓
Send verification email
```

Passwords must never be stored in plaintext.

---

## 4. Login

```text
Login form
    ↓
POST /api/auth/login
    ↓
Auth Service
    ↓
Verify password
    ↓
Create authentication state
    ↓
Authenticated user
```

---

## 5. Authentication

The gateway may receive:

```text
Authorization: Bearer <token>
```

The Auth Service validates the token.

The application should return authenticated user information without exposing sensitive credentials.

---

# 6. Email Verification

After registration:

```text
User
 ↓
Register
 ↓
Auth Service
 ↓
Generate verification token
 ↓
Email Service
 ↓
Verification Email
 ↓
User clicks link
 ↓
Auth Service verifies token
```

Verification tokens should be:

* Random.
* Expiring.
* Single-use.

---

# 7. Forgot Password

The user selects:

```text
Forgot password
```

The frontend sends:

```text
POST /api/auth/forgot-password
```

Example:

```json
{
  "email": "user@example.com"
}
```

The backend should respond generically.

Recommended response:

```text
If an account exists for this email, a reset link has been sent.
```

This prevents attackers from discovering registered accounts.

---

# 8. Reset Token

The backend generates a cryptographically secure token.

Conceptually:

```text
User
 ↓
Forgot password
 ↓
Random reset token
 ↓
Store token + expiration
 ↓
Send email
```

The token should expire after a short period.

Example:

```text
15–60 minutes
```

depending on the security policy.

---

# 9. Reset Email

Example link:

```text
https://echosign.example.com/reset-password?token=<TOKEN>
```

The email should contain a clear call to action.

The token must never be logged unnecessarily.

---

# 10. Password Reset

Frontend submits:

```text
POST /api/auth/reset-password
```

Example:

```json
{
  "token": "...",
  "password": "NewPassword123!"
}
```

The Auth Service:

1. Finds the token.
2. Checks expiration.
3. Checks whether it has already been used.
4. Validates password requirements.
5. Hashes the new password.
6. Updates the user.
7. Invalidates the reset token.

---

# 11. Email Configuration

Mail credentials belong only on the backend.

Typical environment variables:

```text
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
MAIL_FROM=
```

These must never be placed in React environment variables that are bundled into the browser.

---

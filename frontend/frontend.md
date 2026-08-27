# EchoSign Frontend

## 1. Overview

The EchoSign frontend is a React + TypeScript application served through Nginx.

Its responsibilities include:

* Application UI.
* Navigation.
* Authentication pages.
* Registration.
* Login.
* Forgot password.
* Reset password.
* Trial status.
* Translation.
* ASL gloss display.
* Sign animation.
* Fingerspelling.
* Playback controls.

---

## 2. Frontend Stack

The application uses:

* React
* TypeScript
* Vite
* Tailwind CSS
* Motion
* Lucide React
* Puter AI
* LandmarkPlayer

---

## 3. Docker Deployment

The frontend is packaged inside an Nginx container.

```text
Browser
   ↓
localhost:8080
   ↓
Nginx
   ↓
React static files
```

Nginx also proxies API requests toward the backend gateway.

---

## 4. API Rule

Frontend code should use relative API URLs.

Correct:

```ts
fetch("/api/translate")
```

Incorrect:

```ts
fetch("http://127.0.0.1:8000/translate")
```

The second approach is problematic because `127.0.0.1` refers to the browser's host, not the Docker gateway.

The correct architecture is:

```text
React
 ↓
/api/translate
 ↓
Nginx
 ↓
Gateway :8000
 ↓
Translation Service :8003
```

---

# 5. Translate Page

The Translate page allows users to enter text and receive an ASL representation.

Supported source languages include:

```text
English
French
Arabic
Spanish
German
Italian
Portuguese
Turkish
```

---

## 6. Translation Pipeline

For English:

```text
English
  ↓
Translation Service
  ↓
ASL Gloss
```

For another language:

```text
French / Arabic / Spanish / ...
             ↓
          Puter AI
             ↓
          English
             ↓
    Translation Service
             ↓
          ASL Gloss
```

---

## 7. Puter AI Translation

When the selected language is not English, the frontend asks Puter AI to produce a faithful English translation.

The prompt requires:

* Complete meaning.
* No summarization.
* No removed names.
* No removed words.
* Natural English.
* Translation only.

The frontend supports both string responses and structured Puter responses containing `message.content`.

---

## 8. ASL Translation Request

The English text is sent to:

```text
POST /api/translate
```

Example:

```ts
const response = await fetch("/api/translate", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    text: englishText,
  }),
});
```

The response contains:

```json
{
  "gloss": "HELLO HOW YOU"
}
```

---

## 9. Gloss Processing

The frontend converts the gloss into uppercase words:

```ts
const words = gloss
  .trim()
  .toUpperCase()
  .split(/\s+/);
```

The current word is stored in:

```ts
currentWord
```

The current fingerspelled letter is stored in:

```ts
currentLetter
```

---

## 10. Sign Dictionary

The frontend loads:

```text
idx2gloss_cache.json
```

and creates:

```ts
const GLOSS_DICT = new Set(
  Object.values(idx2gloss).map(
    (word) => word.toUpperCase()
  )
);
```

If a gloss word exists in the dictionary, the application considers it a known sign.

---

## 11. Known Sign

Known words are rendered using:

```tsx
<LandmarkPlayer
  word={current}
  playing={playing}
/>
```

These words are presented as dedicated ASL signs.

---

## 12. Unknown Sign

Unknown words are converted into letters:

```ts
const letters = word
  .split("")
  .filter((c) => c !== " ");
```

Each letter is rendered using:

```tsx
<LetterLandmarkPlayer
  letter={letters[currentLetter]}
  playing={playing}
/>
```

The user can therefore see the word fingerspelled letter by letter.

---

## 13. Playback

The page supports:

* Play.
* Pause.
* Reset.
* Speed control.
* Letter selection.

The speed slider controls the fingerspelling interval.

Current range:

```text
200 ms → 1400 ms
```

---

## 14. Quick Picks

The page can provide predefined phrases that follow the same pipeline:

```text
Input
 ↓
Natural language → English
 ↓
English → ASL Gloss
 ↓
Gloss → Sign
```

---

# 15. Authentication UI

The frontend should provide:

```text
/login
/register
/forgot-password
/reset-password
```

Authentication state should be centralized.

Recommended structure:

```text
AuthProvider
    │
    ├── user
    ├── loading
    ├── login()
    ├── register()
    └── logout()
```

---

# 16. Forgot Password UI

The user enters their email.

Frontend sends:

```text
POST /api/auth/forgot-password
```

The response should always display a generic message such as:

```text
If an account exists for this email, a reset link has been sent.
```

This prevents account enumeration.

---

# 17. Reset Password UI

The email contains a link similar to:

```text
/reset-password?token=...
```

The frontend reads the token and sends:

```text
POST /api/auth/reset-password
```

with:

```json
{
  "token": "...",
  "password": "..."
}
```

---

# 18. Trial Integration

The frontend obtains trial state through:

```text
GET /api/trial/status
```

and consumes a trial through:

```text
POST /api/trial/consume
```

Requests should include browser credentials:

```ts
fetch("/api/trial/status", {
  credentials: "include",
});
```

The frontend must never treat local React state as the source of truth for trial usage.

---

# 19. Recommended API Helper

A centralized helper is recommended:

```ts
export async function apiFetch(
  path: string,
  options: RequestInit = {},
) {
  return fetch(`/api${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
}
```

Then:

```ts
apiFetch("/trial/status");
```

or:

```ts
apiFetch("/trial/consume", {
  method: "POST",
});
```

---

# 20. Browser Security

Never store passwords in:

```text
localStorage
sessionStorage
React state permanently
```

Authentication tokens should preferably use secure server-managed cookies where appropriate.

---

# 21. Frontend Environment

The frontend should not contain:

* SMTP credentials.
* Redis credentials.
* JWT signing secrets.
* Private API keys.
* Internal Docker hostnames.

The frontend only needs public API routes.

# EchoSign API Gateway

## 1. Purpose

The API Gateway is the central backend entry point for the frontend.

It hides Docker-internal services from the browser.

---

## 2. Architecture

```text
Browser
   ↓
Nginx :8080
   ↓
Gateway :8000
   ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Auth :8001   │ Sign :8002   │ Translation  │ Trial :8004  │
│              │              │ :8003        │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 3. Trial Proxy

The gateway exposes:

```text
/trial/{path}
```

and forwards to:

```text
http://trial-service:8004/trial/{path}
```

For example:

```text
/api/trial/status
        ↓
Gateway
        ↓
trial-service:8004/trial/status
```

---

## 4. Request Forwarding

The gateway should forward:

* HTTP method.
* Request body.
* Query parameters.
* Authorization header.
* Cookie header.
* Content headers where appropriate.

The `Host` header should not be blindly forwarded.

---

## 5. Cookie Forwarding

This is critical for the anonymous trial system.

The browser sends:

```text
Cookie: echosign_trial_id=...
```

The gateway must forward it to the Trial Service.

When the Trial Service creates a new identity, it returns:

```text
Set-Cookie: echosign_trial_id=...
```

The gateway must return that `Set-Cookie` header to the browser.

Without this, every request can appear to originate from a new anonymous browser.

---

## 6. Translation Proxy

The gateway should expose:

```text
/api/translate
```

and forward it to:

```text
translation-service:8003/translate
```

The frontend therefore never needs to know the Docker hostname.

---

## 7. Authentication Proxy

Authentication requests should follow:

```text
/api/auth/*
       ↓
Gateway
       ↓
auth-service:8001
```

---

## 8. Gateway Security

The gateway should be the only backend service exposed to the frontend network.

Internal services should communicate over Docker's internal network.

Redis should never be publicly exposed in production.

---

## 9. Error Handling

The gateway should preserve downstream HTTP status codes.

Examples:

```text
200 → success
400 → invalid request
401 → authentication required
403 → forbidden / trial exhausted
404 → endpoint not found
500 → backend failure
```

The frontend can then respond appropriately.

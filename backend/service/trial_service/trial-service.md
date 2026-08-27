# EchoSign Trial Service

## 1. Purpose

The Trial Service controls anonymous free usage.

The current policy is:

```text
5 free trials
30-day lifetime for the anonymous trial identity
```

---

## 2. Configuration

```python
TRIAL_LIMIT = 5
TRIAL_TTL_SECONDS = 60 * 60 * 24 * 30
```

Which equals:

```text
30 days
```

---

# 3. Anonymous Identity

The browser receives:

```text
echosign_trial_id
```

This cookie identifies the anonymous user.

It is configured as:

```text
HttpOnly
SameSite=Lax
Path=/
```

Production should additionally use:

```text
Secure
```

when HTTPS is enabled.

---

# 4. Redis

Each anonymous identity gets a Redis key:

```text
echosign:trial:<trial_id>
```

Example:

```text
echosign:trial:abc123...
```

Value:

```text
5
```

After one consumption:

```text
4
```

---

# 5. Trial Status

Endpoint:

```text
GET /trial/status
```

Browser-facing route:

```text
GET /api/trial/status
```

Example:

```json
{
  "authenticated": false,
  "trial_used": true,
  "trials_remaining": 4,
  "requires_login": false
}
```

---

# 6. Trial Consumption

Endpoint:

```text
POST /trial/consume
```

Browser-facing:

```text
POST /api/trial/consume
```

The Trial Service uses Redis `DECR`.

This is important because Redis performs the decrement atomically.

---

# 7. Trial Exhaustion

When:

```text
trials_remaining = 0
```

the API returns:

```text
requires_login = true
```

The frontend should then request authentication.

---

# 8. Authenticated Users

Authenticated users do not consume anonymous trials.

Conceptually:

```text
Authenticated
     ↓
No anonymous trial counter
```

---

# 9. Cookie Persistence

The browser must retain:

```text
echosign_trial_id
```

The gateway must preserve:

```text
Cookie
Set-Cookie
```

The request chain is:

```text
Browser
 ↓
Nginx
 ↓
Gateway
 ↓
Trial Service
 ↓
Redis
```

---

# 10. Testing

Create a cookie jar:

```powershell
curl.exe -i -c cookies.txt http://localhost:8080/api/trial/status
```

Then consume:

```powershell
curl.exe -i -c cookies.txt -b cookies.txt -X POST http://localhost:8080/api/trial/consume
```

Then check:

```powershell
curl.exe -i -c cookies.txt -b cookies.txt http://localhost:8080/api/trial/status
```

Expected sequence:

```text
5
↓
4
↓
3
↓
2
↓
1
↓
0
```

---


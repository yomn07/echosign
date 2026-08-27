from fastapi import (
    FastAPI,
    Request,
    Response,
)

from trial import (
    TRIAL_COOKIE_NAME,
    get_or_create_trial,
    get_remaining_trials,
    consume_trial,
)

from security import (
    get_user_from_token,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="EchoSign Trial Service",
    version="1.0.0",
)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "service": "trial-service",
        "status": "healthy",
    }


# ============================================================
# AUTHENTICATION
# ============================================================

def get_authenticated_user(
    request: Request,
):

    authorization = request.headers.get(
        "Authorization"
    )

    if not authorization:
        return None

    scheme, _, token = authorization.partition(
        " "
    )

    if (
        scheme.lower() != "bearer"
        or not token
    ):
        return None

    return get_user_from_token(
        token
    )


# ============================================================
# TRIAL STATUS
# ============================================================

@app.get("/trial/status")
def trial_status(
    request: Request,
    response: Response,
):

    # --------------------------------------------------------
    # AUTHENTICATED USER
    # --------------------------------------------------------

    user = get_authenticated_user(
        request
    )

    if user:

        return {
            "authenticated": True,

            "user": user,

            "trial_used": False,

            "trials_remaining": None,

            "requires_login": False,
        }


    # --------------------------------------------------------
    # ANONYMOUS USER
    # --------------------------------------------------------

    trial_id = request.cookies.get(
        TRIAL_COOKIE_NAME
    )


    trial_id, created = get_or_create_trial(
        trial_id
    )


    # --------------------------------------------------------
    # First visit:
    # create persistent browser cookie.
    # --------------------------------------------------------

    if created:

        response.set_cookie(
            key=TRIAL_COOKIE_NAME,

            value=trial_id,

            max_age=60 * 60 * 24 * 30,

            httponly=True,

            samesite="lax",

            secure=False,

            path="/",
        )


    # --------------------------------------------------------
    # Read current Redis counter.
    # --------------------------------------------------------

    remaining = get_remaining_trials(
        trial_id
    )


    return {
        "authenticated": False,

        "trial_used":
            remaining < 5,

        "trials_remaining":
            remaining,

        "requires_login":
            remaining <= 0,
    }


# ============================================================
# CONSUME TRIAL
# ============================================================

@app.post("/trial/consume")
def trial_consume(
    request: Request,
    response: Response,
):

    # --------------------------------------------------------
    # AUTHENTICATED USER
    # --------------------------------------------------------

    user = get_authenticated_user(
        request
    )

    if user:

        return {
            "authenticated": True,

            "trial_used": False,

            "trials_remaining": None,

            "requires_login": False,
        }


    # --------------------------------------------------------
    # ANONYMOUS USER
    # --------------------------------------------------------

    trial_id = request.cookies.get(
        TRIAL_COOKIE_NAME
    )


    trial_id, created = get_or_create_trial(
        trial_id
    )


    # --------------------------------------------------------
    # If this is the first request, persist
    # the generated trial ID.
    # --------------------------------------------------------

    if created:

        response.set_cookie(
            key=TRIAL_COOKIE_NAME,

            value=trial_id,

            max_age=60 * 60 * 24 * 30,

            httponly=True,

            samesite="lax",

            secure=False,

            path="/",
        )


    # --------------------------------------------------------
    # Consume exactly ONE trial.
    # --------------------------------------------------------

    remaining = consume_trial(
        trial_id
    )


    return {
        "authenticated": False,

        "trial_used": True,

        "trials_remaining":
            remaining,

        "requires_login":
            remaining <= 0,
    }

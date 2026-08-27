import secrets

from fastapi import HTTPException, Request, Response

from config import (
    TRIAL_LIMIT,
    TRIAL_TTL_SECONDS,
)

from redis_client import redis_client


TRIAL_COOKIE_NAME = "echosign_trial_id"


# ============================================================
# CREATE TRIAL ID
# ============================================================

def create_trial_id() -> str:
    return secrets.token_urlsafe(32)


# ============================================================
# REDIS KEY
# ============================================================

def get_trial_key(
    trial_id: str,
) -> str:

    return f"echosign:trial:{trial_id}"


# ============================================================
# GET OR CREATE TRIAL
# ============================================================

def get_or_create_trial(
    trial_id: str | None,
) -> tuple[str, bool]:

    if trial_id:
        return trial_id, False

    return create_trial_id(), True


# ============================================================
# GET REMAINING TRIALS
# ============================================================

def get_remaining_trials(
    trial_id: str,
) -> int:

    key = get_trial_key(
        trial_id
    )

    value = redis_client.get(
        key
    )

    if value is None:
        return TRIAL_LIMIT

    return max(
        0,
        int(value),
    )


# ============================================================
# CONSUME ONE TRIAL
# ============================================================

def consume_trial(
    trial_id: str,
) -> int:

    key = get_trial_key(
        trial_id
    )

    # --------------------------------------------------------
    # Initialize counter on first use.
    # --------------------------------------------------------

    redis_client.set(
        key,
        TRIAL_LIMIT,
        nx=True,
        ex=TRIAL_TTL_SECONDS,
    )

    # --------------------------------------------------------
    # Atomically consume one trial.
    # --------------------------------------------------------

    remaining = redis_client.decr(
        key
    )

    # --------------------------------------------------------
    # Never allow negative values.
    # --------------------------------------------------------

    if remaining < 0:

        redis_client.set(
            key,
            0,
            ex=TRIAL_TTL_SECONDS,
        )

        raise HTTPException(
            status_code=403,
            detail={
                "code": "TRIAL_EXHAUSTED",

                "message":
                    "Your 5 free trials have been used. "
                    "Please sign in to continue.",

                "requires_login": True,
            },
        )

    return remaining

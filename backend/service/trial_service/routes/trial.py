from fastapi import (
    APIRouter,
    Request,
    Response,
)

from trial import (
    consume_trial,
    get_trial_status,
)


router = APIRouter(
    prefix="/trial",
    tags=["Trial"],
)


# ============================================================
# STATUS
# ============================================================

@router.get("/status")
def trial_status(
    request: Request,
    response: Response,
):

    status = get_trial_status(
        request,
        response,
    )

    return {
        "authenticated": False,

        **status,

        "requires_login":
            status["trials_remaining"] <= 0,
    }


# ============================================================
# CONSUME
# ============================================================

@router.post("/consume")
def trial_consume(
    request: Request,
    response: Response,
):

    result = consume_trial(
        request,
        response,
    )

    return {
        "authenticated": False,

        **result,

        "requires_login":
            result["trials_remaining"] <= 0,
    }

from .translation import router as translation_router
from .landmarks import router as landmarks_router

__all__ = [
    "translation_router",
    "landmarks_router",
]
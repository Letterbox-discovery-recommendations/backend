from .recommendations import router as recommendations_router
from .rankings import router as rankings_router
from .visits import router as visits_router

__all__ = ["recommendations_router", "rankings_router", "visits_router"]

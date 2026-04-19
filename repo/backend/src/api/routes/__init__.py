from fastapi import APIRouter

from . import admin, attendance, auth, bargaining, candidates, documents, idp, orders, payment, queue, refunds

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(idp.router)
api_router.include_router(candidates.router)
api_router.include_router(documents.router)
api_router.include_router(orders.router)
api_router.include_router(payment.router)
api_router.include_router(bargaining.router)
api_router.include_router(refunds.router)
api_router.include_router(attendance.router)
api_router.include_router(queue.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]

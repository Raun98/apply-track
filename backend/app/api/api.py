from fastapi import APIRouter

from app.api.v1 import auth, applications, email_accounts, webhooks, board, subscriptions, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(email_accounts.router, prefix="/email-accounts", tags=["email-accounts"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(board.router, prefix="/board", tags=["board"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

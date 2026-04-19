"""
Internal identity-provider routes.

Issues client-credentials JWTs to trusted local clients and exposes the
public signing key via JWKS. External IdPs are not supported.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...persistence.database import get_db
from ...persistence.repositories.auth_repo import AuthRepository
from ...schemas.auth import IdpTokenRequest, IdpTokenResponse
from ...schemas.common import SuccessResponse, make_success
from ...security import idp as idp_mod
from ...security import jwt as jwt_mod
from ...security.errors import AuthError

router = APIRouter(prefix="/idp", tags=["idp"])


@router.post("/token", response_model=SuccessResponse[IdpTokenResponse])
async def issue_token(
    payload: IdpTokenRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if payload.grant_type != "client_credentials":
        raise AuthError("Unsupported grant_type.")
    repo = AuthRepository(session)
    client = await repo.get_idp_client(payload.client_id)
    if client is None or not client.is_active:
        raise AuthError("Client is not recognised.")
    if not idp_mod.verify_client_secret(payload.client_secret, client.client_secret_hash):
        raise AuthError("Client credentials are invalid.")
    granted = idp_mod.parse_scope(payload.scope, client.allowed_scopes)
    ttl_seconds = 15 * 60
    token = idp_mod.build_client_credentials_token(
        client_id=client.client_id, scopes=granted, ttl_seconds=ttl_seconds
    )
    data = IdpTokenResponse(
        access_token=token, expires_in=ttl_seconds, scope=" ".join(granted)
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.get("/jwks", response_model=dict)
async def jwks() -> dict:
    return jwt_mod.get_jwks()

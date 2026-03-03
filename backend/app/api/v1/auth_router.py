"""
Urban Cortex AI – Auth Router
===============================

Authentication endpoints.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse, UserProfile
from app.services.auth_service import AuthService
from app.utils.response_formatter import success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthService()


# ── POST /api/v1/auth/signup ───────────────────────────────────

@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    summary="Register new citizen user",
)
async def signup(request: SignupRequest):
    """
    Register new citizen user.
    
    - Hashes password
    - Creates user in Firestore
    - Default role: citizen
    """
    user = await auth_service.signup(
        name=request.name,
        email=request.email,
        password=request.password,
        city=request.city
    )
    
    profile = auth_service.format_user_profile(user)
    
    return success_response(
        data=profile,
        message="User registered successfully",
    )


# ── POST /api/v1/auth/login ────────────────────────────────────

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Login and get JWT token",
)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT access token.
    
    - Verifies email and password
    - Generates JWT token
    - Returns access_token
    """
    access_token = await auth_service.login(
        email=request.email,
        password=request.password
    )
    
    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer"
        },
        message="Login successful",
    )


# ── GET /api/v1/auth/me ────────────────────────────────────────

@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get authenticated user's profile.
    
    Requires: Authorization: Bearer <token>
    """
    profile = auth_service.format_user_profile(current_user)
    
    return success_response(
        data=profile,
        message="User profile retrieved",
    )

"""
Urban Cortex AI – Auth Schemas
================================

Pydantic models for authentication endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, EmailStr


# ── Signup Request ─────────────────────────────────────────────

class SignupRequest(BaseModel):
    """Request body for POST /api/v1/auth/signup"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)


# ── Login Request ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Request body for POST /api/v1/auth/login"""
    email: EmailStr = Field(...)
    password: str = Field(...)


# ── Token Response ─────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Response for successful login"""
    access_token: str = Field(...)
    token_type: str = Field(default="bearer")


# ── User Profile ───────────────────────────────────────────────

class UserProfile(BaseModel):
    """Complete user profile"""
    user_id: str
    name: str
    email: EmailStr
    role: str
    assigned_truck_id: Optional[str] = None
    city: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

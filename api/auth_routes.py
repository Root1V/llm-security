import logging
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse

from core.dependecies import get_users
from security.auth import verify_basic_credentials, verify_user_password
from security.tokens import generate_token, verify_token

router = APIRouter(tags=["auth"])

logger = logging.getLogger("api.auth.routes")

@router.post("/login")
async def web_login(
    username: str = Form(...), 
    password: str = Form(...),
    users: dict = Depends(get_users)):
    """
    Login para usuarios web (form-based).
    Solo roles user/monitoring.
    """

    logger.debug(f"Attempting web login for user: {username}")
    verify_user_password(username, password, users)

    user = users.get(username)
    role = user.get("role")

    if role not in {"user", "monitoring"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail={
                "code": "ROLE_NOT_ALLOWED",
                "message": "Role not allowed for web login"
            })

    token, _ = generate_token(username, role)

    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=False,  # PROD: True
        samesite="Lax",
    )
    return response


@router.post("/llm/login")
async def llm_login(
    credentials = Depends(verify_basic_credentials),
    users: dict = Depends(get_users),
):
    """
    Login para agentes IA.
    """
    logger.debug(f"Attempting LLM login for user: {credentials}")
    user = users.get(credentials)
    role = user.get("role")

    if role not in {
        "agent_reasoning",
        "agent_fast",
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User role not authorized for LLM login")

    token, exp = generate_token(credentials, role)
    return {"token": token, "expires_in": exp}


@router.post("/validate")
async def validate_token(
    payload: dict,
):
    """
    Endpoint usado por NGINX (auth_request o subrequest)
    """
    logger.debug("Validating token via /validate endpoint")

    token = payload.get("token")
    if not token:
        return JSONResponse({"valid": False}, status_code=status.HTTP_401_UNAUTHORIZED)

    is_valid = verify_token(token)
    return JSONResponse({"valid": is_valid}, status_code=status.HTTP_200_OK if is_valid else status.HTTP_401_UNAUTHORIZED)

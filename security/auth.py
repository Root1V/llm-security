import logging
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from core.dependecies import get_users

security = HTTPBasic()
logger = logging.getLogger("security.auth")


def verify_basic_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
    users: dict = Depends(get_users),
) -> str:
    
    logger.debug("Verifying credentials for user: %s", credentials.username)
    user = users.get(credentials.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    expected_password = user.get("password")
    if not expected_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not secrets.compare_digest(credentials.password, expected_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return credentials.username


def verify_user_password(
    username: str,
    password: str,
    users: dict,
) -> None:
    """
    Verifica username + password.
    No retorna nada si es correcto.
    Lanza HTTPException si falla.
    """

    logger.debug("Verifying username and password for user: %s", username)
    user = users.get(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS_USERNAME",
                "message": "Invalid Credentials - username"
            }
        )

    stored_password = user.get("password")
    if not stored_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_SET_CREDENTIALS_PASSWORD",
                "message": "Invalid Set Credentials - password"
            }
        )

    if not secrets.compare_digest(password, stored_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS_PASSWORD",
                "message": "Invalid Credentials - password"
            },
        )
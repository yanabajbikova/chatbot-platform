from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
import secrets

security = HTTPBasic()

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")


def admin_required(credentials: HTTPBasicCredentials = Depends(security)):
    correct_login = secrets.compare_digest(credentials.username, ADMIN_LOGIN)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)

    if not (correct_login and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Доступ запрещён",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
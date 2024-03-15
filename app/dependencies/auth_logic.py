# File: app/dependencies/auth.py

from fastapi import Security, HTTPException
from fastapi.security import HTTPBasicCredentials
from app.utils.auth_utils import get_current_user
from fastapi import status

def verify_user_role(user: dict = Security(get_current_user), required_role: str = "admin"):
    if required_role in user.get('roles', []):
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough permissions to access this resource",
        )

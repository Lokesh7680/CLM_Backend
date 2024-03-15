from functools import wraps
from fastapi import Request, HTTPException, status, Depends
from pymongo import MongoClient
from app.utils.auth_utils import verify_user_role

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        async def decorated_view(request: Request, *args, **kwargs):
            # Adjust to use admin_id from the request
            admin_id = request.json().get('admin_id', None)
            if not admin_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access, no admin_id provided")

            mongo_uri = "mongodb://localhost:27017/"
            client = MongoClient(mongo_uri)
            db = client['Clm_db']

            user = db.users.find_one({"admin_id": admin_id})
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            user_roles = user.get('roles', [])
            if any(role in user_roles for role in roles):
                return await fn(request, *args, **kwargs)
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied, insufficient permissions")

        return decorated_view
    return wrapper


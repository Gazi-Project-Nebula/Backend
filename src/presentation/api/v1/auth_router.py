from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from src.application import schemas
from src.application.services.auth_service import AuthService
from src.presentation.dependencies import get_auth_service, get_current_user, verify_admin_user

router = APIRouter()

@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    try:
        return auth_service.register_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(get_auth_service)):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_user_token(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/auth/login", response_model=schemas.User)
def login(user_credentials: schemas.UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    user = auth_service.authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    return user

@router.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    try:
        auth_service.register_user(user)
        return Response(status_code=status.HTTP_201_CREATED)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@router.get("/api/users", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: schemas.User = Depends(verify_admin_user),
):
    return auth_service.get_users(skip=skip, limit=limit)

@router.put("/api/users/{user_id}/role", response_model=schemas.User)
def update_user_role(
    user_id: int,
    user_role: schemas.UserRoleUpdate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: schemas.User = Depends(verify_admin_user),
):
    updated_user = auth_service.update_user_role(user_id, user_role.role)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: schemas.User = Depends(verify_admin_user),
):
    user = auth_service.user_repo.get_by_id(user_id) # Using repo directly or add 'get_user' to service. 
  
    if not auth_service.user_repo.get_by_id(user_id):
         raise HTTPException(status_code=404, detail="User not found")
    auth_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

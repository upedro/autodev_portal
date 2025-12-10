"""
Authentication router
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from database import get_database
from models import UsuarioLogin, UsuarioCreate, UsuarioResponse
from utils.auth import hash_password, verify_password, create_access_token
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
async def login(credentials: UsuarioLogin, db=Depends(get_database)):
    """
    Authenticate user and return JWT token

    Args:
        credentials: User login credentials
        db: Database instance

    Returns:
        Access token and user information
    """
    try:
        # Find user by email
        user = await db.usuarios.find_one({"email": credentials.email})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(credentials.senha, user["senha_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.get("ativo", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Create access token
        access_token = create_access_token(data={"sub": str(user["_id"])})

        # Prepare user response
        user_response = {
            "id": str(user["_id"]),
            "nome": user["nome"],
            "email": user["email"],
            "ativo": user.get("ativo", True),
            "created_at": user.get("created_at", datetime.utcnow()).isoformat(),
        }

        logger.info(f"User {credentials.email} logged in successfully")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UsuarioCreate, db=Depends(get_database)):
    """
    Register a new user

    Args:
        user_data: User registration data
        db: Database instance

    Returns:
        Created user information
    """
    try:
        # Check if email already exists
        existing_user = await db.usuarios.find_one({"email": user_data.email})

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password
        senha_hash = hash_password(user_data.senha)

        # Create user document
        user_doc = {
            "nome": user_data.nome,
            "email": user_data.email,
            "senha_hash": senha_hash,
            "ativo": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Insert user
        result = await db.usuarios.insert_one(user_doc)

        # Prepare response
        user_response = UsuarioResponse(
            id=str(result.inserted_id),
            nome=user_data.nome,
            email=user_data.email,
            ativo=True,
            created_at=user_doc["created_at"],
        )

        logger.info(f"New user registered: {user_data.email}")

        return user_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

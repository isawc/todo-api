from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def cadastrar_usuario(usuario: schemas.UserCreate, db: Session = Depends(get_db)):

    # Verifica se o email já existe no banco
    email_existe = db.query(models.User).filter(
        models.User.email == usuario.email
    ).first()

    if email_existe:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Verifica se o username já existe no banco
    username_existe = db.query(models.User).filter(
        models.User.username == usuario.username
    ).first()

    if username_existe:
        raise HTTPException(status_code=400, detail="Username já cadastrado")

    # Gera o hash da senha antes de salvar
    senha_hash = auth.gerar_hash_senha(usuario.password)
    novo_usuario = models.User(
        email=usuario.email,
        username=usuario.username,
        hashed_password=senha_hash,
    )

    # Salva no banco
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario) 

    return novo_usuario


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    # Tenta autenticar o usuário
    usuario = auth.autenticar_usuario(db, form_data.username, form_data.password)

    # Se retornou None, usuário ou senha errados
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )

    # Gera o token JWT com o username dentro
    token = auth.criar_token(
        dados={"sub": usuario.username},
        expira_em=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def meu_perfil(usuario_atual=Depends(auth.get_usuario_atual)):
    # Depends já busca e valida o usuário pelo token
    # se chegar aqui, o usuário está autenticado
    return usuario_atual
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

SECRET_KEY = "chave-isaac"
ALGORITHM = "HS256"  # algoritmo de criptografia do token
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token expira em 30 minutos

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    # Compara a senha digitada com o hash salvo no banco
    return pwd_context.verify(senha_pura, senha_hash)


def gerar_hash_senha(senha: str) -> str:
    # Transforma a senha pura em hash antes de salvar
    return pwd_context.hash(senha)


def criar_token(dados: dict, expira_em: Optional[timedelta] = None) -> str:
    # Faz uma cópia dos dados pra não modificar o original
    payload = dados.copy()

    # Define quando o token vai expirar
    expiracao = datetime.utcnow() + (expira_em or timedelta(minutes=15))
    payload.update({"exp": expiracao})

    # Gera e retorna o token assinado
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def buscar_usuario_por_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def autenticar_usuario(db: Session, username: str, senha: str):
    usuario = buscar_usuario_por_username(db, username)

    # Se não achou o usuário ou a senha tiver errada, retorna None
    if not usuario or not verificar_senha(senha, usuario.hashed_password):
        return None

    return usuario


def get_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    # Erro padrão pra token inválido
    erro_credencial = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decodifica o token e pega o username de dentro
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise erro_credencial

    except JWTError:
        raise erro_credencial

    # Busca o usuário no banco com o username do token
    usuario = buscar_usuario_por_username(db, username)

    if usuario is None:
        raise erro_credencial

    return usuario
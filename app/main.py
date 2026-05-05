from fastapi import FastAPI

from app.database import engine, Base
from app.routers import auth, tasks

# Cria todas as tabelas no banco ao iniciar a aplicação
# O SQLAlchemy lê os models e gera o SQL automaticamente
Base.metadata.create_all(bind=engine)

# Cria a aplicação FastAPI
app = FastAPI(
    title="Todo API",
    description="API de gerenciamento de tarefas com autenticação JWT",
    version="1.0.0",
)

# Registra os routers na aplicação
app.include_router(auth.router)
app.include_router(tasks.router)


# Rota raiz só pra confirmar que tá rodando
@app.get("/")
def root():
    return {"mensagem": "Todo API rodando!"}
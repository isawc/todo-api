from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/tasks", tags=["Tarefas"])


# CREATE - cria uma nova tarefa
@router.post("/", response_model=schemas.TaskResponse, status_code=201)
def criar_tarefa(
    tarefa: schemas.TaskCreate,
    db: Session = Depends(get_db),
    usuario_atual=Depends(auth.get_usuario_atual),  # exige login
):
    nova_tarefa = models.Task(
        title=tarefa.title,
        description=tarefa.description,
        owner_id=usuario_atual.id,  # liga a tarefa ao usuário logado
    )

    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)

    return nova_tarefa


# READ - lista todas as tarefas do usuário logado
@router.get("/", response_model=List[schemas.TaskResponse])
def listar_tarefas(
    db: Session = Depends(get_db),
    usuario_atual=Depends(auth.get_usuario_atual),
):
    # Filtra só as tarefas do usuário logado
    tarefas = db.query(models.Task).filter(
        models.Task.owner_id == usuario_atual.id
    ).all()

    return tarefas


# READ - busca uma tarefa específica pelo id
@router.get("/{tarefa_id}", response_model=schemas.TaskResponse)
def buscar_tarefa(
    tarefa_id: int,
    db: Session = Depends(get_db),
    usuario_atual=Depends(auth.get_usuario_atual),
):
    tarefa = db.query(models.Task).filter(
        models.Task.id == tarefa_id,
        models.Task.owner_id == usuario_atual.id,  # garante que é do usuário logado
    ).first()

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return tarefa


# UPDATE - atualiza uma tarefa
@router.put("/{tarefa_id}", response_model=schemas.TaskResponse)
def atualizar_tarefa(
    tarefa_id: int,
    dados: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    usuario_atual=Depends(auth.get_usuario_atual),
):
    tarefa = db.query(models.Task).filter(
        models.Task.id == tarefa_id,
        models.Task.owner_id == usuario_atual.id,
    ).first()

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    # Atualiza só os campos que vieram na requisição
    # exclude_unset=True ignora os campos que não foram enviados
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(tarefa, campo, valor)  # equivale a tarefa.campo = valor

    db.commit()
    db.refresh(tarefa)

    return tarefa


# DELETE - deleta uma tarefa
@router.delete("/{tarefa_id}", status_code=204)
def deletar_tarefa(
    tarefa_id: int,
    db: Session = Depends(get_db),
    usuario_atual=Depends(auth.get_usuario_atual),
):
    tarefa = db.query(models.Task).filter(
        models.Task.id == tarefa_id,
        models.Task.owner_id == usuario_atual.id,
    ).first()

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    db.delete(tarefa)
    db.commit()
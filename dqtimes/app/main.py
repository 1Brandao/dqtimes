import os
import io
import asyncio
import json
import dask.dataframe as dd
import tempfile
from datetime import timedelta
from dask.distributed import Client, LocalCluster
from app import forecast_temp
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.redis_client import validate_redis_connection
from app.api_monitor import router as monitor_router
from app.auth import (
    get_db, 
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_user
)
from app.db import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.api_monitor import router as monitor_router
import math
import time

# Iniciar um cluster local e um cliente Dask
cluster = LocalCluster()
client = Client(cluster)

app = FastAPI(title="DQTimes API")

# Configurar CORS para permitir requisições do frontend (permissivo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=False,  # Deve ser False quando allow_origins é ["*"]
    allow_methods=["*"],  # Permite todos os métodos HTTP
    allow_headers=["*"],  # Permite todos os headers
    expose_headers=["*"],  # Expõe todos os headers
)

app.include_router(monitor_router)


@app.on_event("startup")
async def startup_event():
    """Executado na inicialização da aplicação"""
    print("🚀 Iniciando DQTimes API...")
    
    # Validar conexão Redis
    if validate_redis_connection():
        print("✅ Redis disponível")
    else:
        print("⚠️ Aviso: Redis não está disponível")


@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    from app.redis_client import get_redis_client
    
    redis_status = False
    try:
        client = get_redis_client()
        client.ping()
        redis_status = True
    except:
        redis_status = False
    
    return {
        "status": "ok",
        "redis": "connected" if redis_status else "disconnected"
    }


# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário
    
    Args:
        user_data: Dados do usuário (email e senha)
        db: Sessão do banco de dados
        
    Returns:
        Dados do usuário criado (sem senha)
        
    Raises:
        HTTPException 400: Se email já estiver em uso
    """
    # Verificar se usuário já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Criar novo usuário
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica usuário e retorna token JWT
    
    Args:
        user_credentials: Email e senha do usuário
        db: Sessão do banco de dados
        
    Returns:
        Token JWT de acesso
        
    Raises:
        HTTPException 401: Se credenciais inválidas
    """
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token JWT
    from app.config import get_settings
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado
    
    Args:
        current_user: Usuário autenticado (obtido do token JWT)
        
    Returns:
        Dados do usuário atual
    """
    return current_user


# ========== FORECASTING ENDPOINTS ==========

@app.post("/projecao_lista/")
async def upload_file(
    lista_historico: str = Form(...),
    quantidade_projecoes: int = Form(...),
):

    lista_original = json.loads(lista_historico)  # Convertendo para lista

    n = quantidade_projecoes 

    # Chamando a função de previsão
    resultado = forecast_temp(lista_original, n)

    return {
        "projecoes": resultado
    }

@app.post("/projecao_dataframe/")
async def upload_file(
    csv_dataframe: UploadFile = File(...),
    quantidade_projecoes: int = Form(...),
    header: bool = Form(...),
    index_col: bool = Form(...),
    page: int = Query(1, ge=1),  # Número da página, deve ser >= 1
    page_size: int = Query(10, ge=1),  # Tamanho da página, deve ser >= 1
):
    n = quantidade_projecoes

    # Salvar o conteúdo do arquivo em um arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(await csv_dataframe.read())
        tmp_file_path = tmp_file.name

    ddf = dd.read_csv(tmp_file_path, header=0 if header else None)

    if index_col:
        ddf = ddf.drop(ddf.columns[0], axis=1)

    # Calcular o número total de linhas e o número total de páginas
    total_rows = len(ddf)
    total_pages = math.ceil(total_rows / page_size)

    # Verificar se o número da página é válido
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page number out of range")

    # Calcular o índice inicial e final para a paginação
    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    # Aplicar a paginação ao DataFrame
    ddf_paginated = ddf.loc[start_index:end_index]

    start_time = time.time()
    lista_df = []

    for part in ddf_paginated.to_delayed():
        # Converter a partição para um pandas DataFrame e iterar sobre as linhas
        for index, row in part.compute().iterrows():
            lista_df.append(row.tolist())

    # Aplica a função de projeção à lista de listas
    
    resultado = []
    for lista in lista_df:
        projection = forecast_temp(lista, n)
        resultado.append(projection)

    end_time = time.time()
    execution_time = end_time - start_time 

    return {
        "execution_time": execution_time,
        "total_pages": total_pages,
        "current_page": page,
        "projecoes": resultado
    }

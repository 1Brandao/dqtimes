import os
import io
import asyncio
import json
import dask.dataframe as dd
import tempfile
from dask.distributed import Client, LocalCluster
from .aplicacao import forecast_temp
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Header, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
import math
import time
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta

cluster = LocalCluster()
client = Client(cluster)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print(f"Dask Dashboard is available at {client.dashboard_link}")

JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)
ACCESS_EXPIRES_MINUTES = 15
REFRESH_EXPIRES_MS = 7 * 24 * 60 * 60 * 1000

try:
    import bcrypt
    _bcrypt_available = True
except Exception:
    _bcrypt_available = False

def _hash_password(plain: str) -> str:
    if _bcrypt_available:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

def _check_password(plain: str, hashed: str) -> bool:
    if _bcrypt_available:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
    return hashlib.sha256(plain.encode("utf-8")).hexdigest() == hashed

users = [
    {"id": 1, "email": "user@example.com", "passwordHash": _hash_password("password123"), "role": "user"},
    {"id": 2, "email": "admin@example.com", "passwordHash": _hash_password("admin123"), "role": "admin"},
]

refresh_store = {}

def issue_access_token(user: dict) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRES_MINUTES)
    payload = {"user_id": user["id"], "role": user["role"], "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def issue_refresh_token(user_id: int) -> str:
    plain = secrets.token_hex(64)
    hash_value = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    expires_at = int(time.time() * 1000) + REFRESH_EXPIRES_MS
    refresh_store[hash_value] = {"userId": user_id, "expiresAt": expires_at}
    return plain

def log_auth(request: Request, status: str, detail: str) -> None:
    client_ip = request.client.host if request.client else "unknown"
    print(f"[auth] {status} path={request.url.path} ip={client_ip} detail={detail}")

async def authenticate(request: Request, authorization: Optional[str] = Header(None)):
    h = authorization or ""
    parts = h.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        log_auth(request, "unauthenticated", "missing_or_malformed_token")
        raise HTTPException(status_code=401, detail="unauthenticated")
    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        request.state.user = payload
    except Exception:
        log_auth(request, "unauthenticated", "invalid_or_expired_token")
        raise HTTPException(status_code=401, detail="unauthenticated")

def authorize(*roles: str):
    async def _inner(request: Request):
        user = getattr(request.state, "user", None)
        if not user or user.get("role") not in roles:
            log_auth(request, "forbidden", f"role={user.get('role') if user else 'none'}")
            raise HTTPException(status_code=403, detail="forbidden")
    return _inner

@app.post("/projecao_lista/")
async def upload_file(
    lista_historico: str = Form(...),
    quantidade_projecoes: int = Form(...),
    _auth: None = Depends(authenticate),
    _roles: None = Depends(authorize("user", "admin")),
):
    lista_original = json.loads(lista_historico)
    n = quantidade_projecoes
    resultado = forecast_temp(lista_original, n)
    return {"projecoes": resultado}

@app.post("/projecao_dataframe/")
async def upload_file(
    csv_dataframe: UploadFile = File(...),
    quantidade_projecoes: int = Form(...),
    header: bool = Form(...),
    index_col: bool = Form(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    _auth: None = Depends(authenticate),
    _roles: None = Depends(authorize("user", "admin")),
):
    n = quantidade_projecoes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(await csv_dataframe.read())
        tmp_file_path = tmp_file.name
    ddf = dd.read_csv(tmp_file_path, header=0 if header else None)
    if index_col:
        ddf = ddf.drop(ddf.columns[0], axis=1)
    total_rows = len(ddf)
    total_pages = math.ceil(total_rows / page_size)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page number out of range")
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    ddf_paginated = ddf.loc[start_index:end_index]
    start_time = time.time()
    lista_df = []
    for part in ddf_paginated.to_delayed():
        for index, row in part.compute().iterrows():
            lista_df.append(row.tolist())
    resultado = []
    for lista in lista_df:
        projection = forecast_temp(lista, n)
        resultado.append(projection)
    end_time = time.time()
    execution_time = end_time - start_time
    return {"execution_time": execution_time, "total_pages": total_pages, "current_page": page, "projecoes": resultado}

@app.post("/login")
async def login(body: dict, request: Request):
    email = (body or {}).get("email")
    password = (body or {}).get("password") or ""
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        log_auth(request, "invalid_credentials", "user_not_found")
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not _check_password(password, user["passwordHash"]):
        log_auth(request, "invalid_credentials", "wrong_password")
        raise HTTPException(status_code=401, detail="invalid_credentials")
    access_token = issue_access_token(user)
    refresh_token = issue_refresh_token(user["id"])
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer", "expires_in": ACCESS_EXPIRES_MINUTES * 60}

@app.post("/token/refresh")
async def token_refresh(body: dict, request: Request):
    refresh_token = (body or {}).get("refresh_token")
    if not refresh_token:
        log_auth(request, "unauthenticated", "missing_refresh_token")
        raise HTTPException(status_code=401, detail="unauthenticated")
    hash_value = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    entry = refresh_store.get(hash_value)
    if not entry:
        log_auth(request, "unauthenticated", "refresh_not_found")
        raise HTTPException(status_code=401, detail="unauthenticated")
    if int(time.time() * 1000) > entry["expiresAt"]:
        refresh_store.pop(hash_value, None)
        log_auth(request, "unauthenticated", "refresh_expired")
        raise HTTPException(status_code=401, detail="unauthenticated")
    refresh_store.pop(hash_value, None)
    new_refresh = issue_refresh_token(entry["userId"])
    user = next((u for u in users if u["id"] == entry["userId"]), None)
    access_token = issue_access_token(user)
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "Bearer", "expires_in": ACCESS_EXPIRES_MINUTES * 60}

@app.post("/logout")
async def logout(body: dict):
    refresh_token = (body or {}).get("refresh_token")
    if not refresh_token:
        return {"ok": True}
    hash_value = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    refresh_store.pop(hash_value, None)
    return {"ok": True}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_auth(request, "server_error", getattr(exc, "message", str(exc)) or "error")
    return JSONResponse(status_code=500, content={"error": "server_error"})
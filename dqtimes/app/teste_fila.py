from tasks import predict
from db import SessionLocal, Job
import time
import uuid
from datetime import datetime

# 1. Preparar os dados
payload = {
    "series": [10, 20, 30, 40, 50],
    "name_ref": "teste_com_banco_v2",
    "periods": 3
}

# Gera um ID único manualmente para garantir consistência
task_id = str(uuid.uuid4())

print(f"--- Criando Job {task_id} no Banco de Dados ---")

# 2. Criar o registro no Banco (PENDING)
with SessionLocal() as session:
    new_job = Job(
        task_id=task_id,
        status="PENDING",
        created_at=datetime.utcnow(),
        payload=payload
    )
    session.add(new_job)
    session.commit()
    print("Job criado com sucesso (Status: PENDING).")

# 3. Enviar para a fila (usando o mesmo ID)
print("--- Enviando tarefa para o Redis ---")
# Usamos apply_async para forçar o ID que acabamos de criar
task = predict.apply_async(args=[payload], task_id=task_id)

print("--- Aguardando processamento ---")
# Loop de espera (Polling simples)
for i in range(10):
    time.sleep(1)
    with SessionLocal() as session:
        # Recarrega o job do banco para ver se o status mudou
        job = session.query(Job).filter_by(task_id=task_id).first()
        print(f"[{i}s] Status atual no BD: {job.status}")
        
        if job.status in ["SUCCESS", "FAILURE"]:
            print(f"\nRESULTADO FINAL: {job.result}")
            break
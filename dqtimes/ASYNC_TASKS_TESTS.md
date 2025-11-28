# Testes de Tasks Assíncronas

## Validação de Round-Trip Completo

Este documento descreve os testes para validar o fluxo completo de tasks assíncronas.

## Pré-requisitos

### Iniciar Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Iniciar Celery Worker

Terminal 1:
```bash
cd dqtimes
python worker.py worker
```

### Iniciar FastAPI

Terminal 2:
```bash
cd dqtimes
uvicorn app.main:app --reload --port 8000
```

### Iniciar Flower (Opcional)

Terminal 3:
```bash
cd dqtimes
python worker.py flower
```

Dashboard: http://localhost:5555

## Testes de Endpoints

### 1. Criar Task Dummy

Endpoint: POST /tasks/dummy

Request:
```bash
curl -X POST "http://localhost:8000/tasks/dummy" \
  -H "Content-Type: application/json" \
  -d '{"duration": 5}'
```

Response esperado:
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "Task enfileirada com ID abc123-def456-ghi789"
}
```

### 2. Consultar Status da Task - PENDING

Endpoint: GET /tasks/status/{task_id}

Request:
```bash
curl -X GET "http://localhost:8000/tasks/status/abc123-def456-ghi789"
```

Response esperado (task pendente):
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "pending",
  "result": null,
  "error": null
}
```

### 3. Consultar Status da Task - EM EXECUÇÃO

Após alguns segundos:

Response esperado (task em execução):
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "em_execucao",
  "result": null,
  "error": null
}
```

### 4. Consultar Status da Task - CONCLUÍDA

Após 5 segundos:

Response esperado (task concluída):
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "concluida",
  "result": {
    "task_id": "abc123-def456-ghi789",
    "status": "completed",
    "message": "Task dummy executada com sucesso apos 5 segundos",
    "duration": 5
  },
  "error": null
}
```

## Fluxo Round-Trip Completo

### Passo 1: Enviar Request para API

```bash
curl -X POST "http://localhost:8000/tasks/dummy" \
  -H "Content-Type: application/json" \
  -d '{"duration": 10}'
```

Salvar task_id da resposta.

### Passo 2: Task é Enfileirada

Verificar no Flower: http://localhost:5555/tasks

Status inicial: PENDING

### Passo 3: Worker Pega a Task

Logs do worker:
```
[2025-11-28 10:00:00,000: INFO/MainProcess] Task app.tasks.dummy_task[abc123] received
[2025-11-28 10:00:00,001: INFO/ForkPoolWorker-1] Task app.tasks.dummy_task[abc123] started
```

Status no Flower: STARTED

### Passo 4: Task é Executada

Task aguarda duration segundos.

### Passo 5: Task Completa

Logs do worker:
```
[2025-11-28 10:00:10,001: INFO/ForkPoolWorker-1] Task app.tasks.dummy_task[abc123] succeeded
```

Status no Flower: SUCCESS

### Passo 6: Consultar Resultado

```bash
curl -X GET "http://localhost:8000/tasks/status/abc123"
```

Resultado completo retornado.

## Validações

### Status Pendente
- Task criada mas não iniciada
- result: null
- error: null

### Status Em Execução
- Worker processando task
- result: null
- error: null

### Status Concluída
- Task finalizada com sucesso
- result: objeto com dados da execução
- error: null

### Status Falhou
- Task com erro
- result: null
- error: mensagem de erro

## Testes Adicionais

### Task com Duração Variável

```bash
curl -X POST "http://localhost:8000/tasks/dummy" \
  -H "Content-Type: application/json" \
  -d '{"duration": 2}'
```

### Múltiplas Tasks Simultâneas

```bash
for i in {1..5}; do
  curl -X POST "http://localhost:8000/tasks/dummy" \
    -H "Content-Type: application/json" \
    -d '{"duration": 3}' &
done
```

Verificar no Flower que todas foram enfileiradas e processadas.

## Swagger UI

Acessar: http://localhost:8000/docs

Testar endpoints interativamente:
1. Expandir POST /tasks/dummy
2. Clicar em "Try it out"
3. Inserir duration
4. Executar
5. Copiar task_id
6. Expandir GET /tasks/status/{task_id}
7. Inserir task_id
8. Executar múltiplas vezes para ver transição de status

## Verificação de Logs

### Worker Logs

```bash
tail -f worker.log
```

### FastAPI Logs

No terminal do uvicorn, verificar requests recebidos.

### Redis Logs

```bash
docker logs -f <redis_container_id>
```

## Troubleshooting

### Task não executa

Verificar se worker está rodando:
```bash
ps aux | grep celery
```

Verificar conexão com Redis:
```bash
redis-cli ping
```

### Status sempre PENDING

Worker não está processando a fila.

Verificar logs do worker para erros.

### Resultado não aparece

Verificar result_expires em celery_config.py.

Resultado pode ter expirado após 3600s.

## Conclusão

Fluxo validado:
1. Request API recebido
2. Task enfileirada no Redis
3. Worker pega task da fila
4. Task executada
5. Resultado armazenado no Redis
6. API retorna task_id
7. Status consultável via API
8. Resultado recuperável após conclusão

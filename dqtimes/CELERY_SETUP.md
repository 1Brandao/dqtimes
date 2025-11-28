# Celery Setup - Integração com FastAPI

## Visão Geral

Integração do Celery com FastAPI para processamento assíncrono de tarefas de previsão.

### Componentes

- Celery Workers: Processam tarefas de forma assíncrona
- Redis: Broker de mensagens e backend de resultados
- Flower: Dashboard de monitoramento
- Fila forecasts: Fila dedicada para tarefas de previsão

## Arquitetura

```
FastAPI -> Redis <- Celery Workers
                       |
                    Flower (Monitor)
```

## Dependências

Instaladas via requirements.txt:

- celery[redis]
- redis
- flower
- python-dotenv

## Configuração de Ambiente

Copiar .env.example para .env e ajustar valores conforme necessário:

```bash
cp .env.example .env
```

### Variáveis Principais

- REDIS_HOST: Endereço do servidor Redis
- REDIS_PORT: Porta do Redis (padrão 6379)
- REDIS_DB: Banco Redis (padrão 0)
- CELERY_BROKER_URL: URL completa do broker
- CELERY_RESULT_BACKEND: URL do backend de resultados

## Testes Locais

### Pré-requisito

Redis rodando localmente:

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Ou instalar Redis:

```bash
sudo apt install redis
redis-server
```

### Iniciar Worker

Terminal 1:

```bash
cd dqtimes
python worker.py worker
```

Ou diretamente:

```bash
celery -A app.celery_config worker --loglevel=info --concurrency=4 --queues=forecasts
```

### Iniciar Flower

Terminal 2:

```bash
cd dqtimes
python worker.py flower
```

Acessar dashboard: http://localhost:5555

### Parar Workers

Pressionar Ctrl+C no terminal do worker ou flower

## Testes com Docker Compose

### Iniciar todos os serviços

```bash
docker-compose up -d
```

### Verificar status

```bash
docker-compose ps
```

### Logs dos workers

```bash
docker-compose logs -f celery_worker
```

### Logs do Flower

```bash
docker-compose logs -f flower
```

### Parar serviços

```bash
docker-compose down
```

### Parar e remover volumes

```bash
docker-compose down -v
```

## Estrutura de Tarefas

### forecast_task

Processa lista de valores históricos e retorna projeções.

Fila: forecasts

Parâmetros:
- lista_historico: JSON string com valores
- quantidade_projecoes: Número de projeções

### forecast_dataframe_task

Processa DataFrame CSV paginado e retorna projeções.

Fila: forecasts

Parâmetros:
- csv_content: Conteúdo do arquivo CSV
- quantidade_projecoes: Número de projeções
- header: Se possui cabeçalho
- index_col: Se possui coluna de índice
- page: Página atual
- page_size: Tamanho da página

## Monitoramento

### Via Flower

Dashboard: http://localhost:5555

Funcionalidades:
- Workers ativos
- Tarefas em execução
- Histórico de tarefas
- Métricas de performance
- Revogar tarefas

### Via Logs

```bash
docker-compose logs -f celery_worker
```

### Health Check Redis

```bash
docker exec dqtimes-redis redis-cli ping
```

## Configurações Avançadas

### Concorrência

Ajustar número de workers paralelos no docker-compose.yml ou worker.py:

```bash
--concurrency=4
```

### Timeout

Configurado em celery_config.py:

- task_time_limit: 3600 segundos (hard limit)
- task_soft_time_limit: 3300 segundos (soft limit)

### Prefetch

Controla quantas tarefas cada worker pega antecipadamente:

```python
worker_prefetch_multiplier=4
```

### Max Tasks per Child

Worker reinicia após processar N tarefas:

```python
worker_max_tasks_per_child=1000
```

## Troubleshooting

### Worker não conecta ao Redis

Verificar se Redis está rodando:

```bash
docker ps | grep redis
```

Verificar variáveis de ambiente no .env

### Tarefas não aparecem no Flower

Verificar se worker está escutando a fila correta:

```bash
docker-compose logs celery_worker | grep forecasts
```

### Erro de importação de módulos

Reconstruir imagem Docker:

```bash
docker-compose build --no-cache
docker-compose up -d
```

## Próximos Passos

- Integração das tasks no FastAPI endpoints
- Implementação de callbacks para notificações
- Configuração de retry policies
- Setup de monitoramento com Prometheus
- Implementação de dead letter queue

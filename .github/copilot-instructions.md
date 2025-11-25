# DQTimes AI Agent Instructions

## Project Overview
DQTimes is a **time series forecasting API** that migrated from Rust to Python, using **CUDA-accelerated libraries** for high-performance predictions. The system combines Python with pre-compiled CUDA/C++ shared libraries (`.so` files) for GPU-accelerated computations.

**Core architecture**: FastAPI backend + CUDA/C++ libraries + Dask distributed computing + Redis caching + optional Celery workers + TypeScript load balancer.

## Critical Architecture Patterns

### Hybrid Python-CUDA Integration
- **Pre-compiled shared libraries** in `app/libs/*.so` are loaded via `ctypes` in `app/aplicacao.py`
- CUDA kernels (`.cu` files) and C++ utilities (`.cpp` files) are compiled ONCE to `.so` files
- **Never modify Python code that calls these libraries without understanding the C/CUDA signatures**
- Example pattern from `app/aplicacao.py`:
  ```python
  cuda_lib = ctypes.CDLL('app/libs/medias_moveis.so')
  cuda_lib.moving_average.argtypes = [float_pointer, float_pointer_pointer, ...]
  ```

### Dual API Surface
1. **FastAPI** (`app/main.py`): Primary API with endpoints `/projecao_lista/` and `/projecao_dataframe/`
2. **Flask** (`api.py`): Legacy async job queue with Celery integration (status: `/status/<task_id>`)

Both APIs coexist. Use FastAPI for new features. Flask is for backward compatibility.

### Data Flow for Predictions
```
User request → FastAPI endpoint → forecast_temp() in aplicacao.py
→ Splits data (70% train, 30% test via C++ split_list)
→ Runs CUDA kernels (Holt-Winters, Moving Averages)
→ Compares errors (compara_testemunha C++ function)
→ Returns best projection + probability
```

## Essential Build & Run Commands

### Compiling CUDA/C++ Libraries
**CUDA libraries** (from `dqtimes/README.md`):
```bash
nvcc -arch=sm_75 -o app/libs/medias_moveis.so -shared -Xcompiler -fPIC app/libs/medias_moveis.cu
```

**C++ utilities**:
```bash
c++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) app/utils.cpp -o app/libs/utilitarios.so
```

**CRITICAL**: Recompile `.so` files after modifying `.cu` or `.cpp` source files. The Docker image builds these at container creation.

### Running the Service
**Docker Compose** (recommended):
```bash
docker-compose up --build
```
- Backend: `http://localhost:80` (FastAPI) + Dask dashboard on `:8787`
- Redis: `localhost:6379`

**Local development**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 80
```

### Testing the API
```bash
curl -X POST http://localhost:80/projecao_lista/ \
  -F "lista_historico=[1,2,3,4,5,6,7,8,9,10]" \
  -F "quantidade_projecoes=3"
```

## Project-Specific Conventions

### Forecast Algorithm Selection
- System automatically tests **7 different periods** (3, 4, 5, 6, 7, 14, 30) with both Holt-Winters and Moving Averages
- Best method is selected via **MSE comparison against test data** (30% holdout)
- Implemented in `forecast_temp()` - never hardcode a single forecasting method

### Configuration Management
- Environment variables via `app/config.py` with `@lru_cache()` singleton pattern
- Required env vars: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` (set in `docker-compose.yml`)
- Use `get_settings()` function, never direct `os.getenv()` calls

### GPU Platform Constraint
- Dockerfile uses `FROM tensorflow/tensorflow:2.14.0-gpu` with `--platform=linux/amd64`
- All CUDA code targets **sm_75 architecture** (Tesla T4 / RTX 20xx series)
- Do not change platform or CUDA compute capability without testing

## Key Integration Points

### Dask Distributed Computing
- Local cluster initialized at startup: `cluster = LocalCluster(); client = Client(cluster)`
- Used for **DataFrame processing** in `/projecao_dataframe/` endpoint
- Dashboard accessible at `:8787` for monitoring tasks

### Redis Caching Layer
- Connection validation happens at startup (`validate_redis_connection()`)
- Client retrieved via `get_redis_client()` from `app/redis_client.py`
- Currently used for health checks; ready for caching forecast results

### Load Balancer (TypeScript)
- Least-connections algorithm in `loadbalance/src/loadBalance/leastConnection.ts`
- Requires `CLIENT_SERVERS` env var (comma-separated URLs)
- Run with: `npm start` (port 8000 by default)

## Common Gotchas

1. **Shared library paths**: Always use relative paths like `'app/libs/medias_moveis.so'` (not absolute)
2. **Data type mismatches**: CUDA functions expect `float32` numpy arrays - use `dtype=np.float32` explicitly
3. **Memory management**: ctypes requires explicit pointer management; see `forecast_temp()` for patterns
4. **Pagination in DataFrame endpoint**: Uses `ddf.loc[start:end]` on Dask dataframes, not standard slicing
5. **Celery broker URL**: Set `CELERY_BROKER_URL` env var if using Flask API's async features

## Testing Strategy
- Test file: `dqtimes/teste_request.py` for basic API validation
- Unit tests in `app/tests/` (e.g., `test_redis.py`)
- No pytest/unittest framework detected - add one if writing new tests

## Dependencies to Watch
- `pybind11`: Required for C++ bindings (install before compiling)
- `dask[distributed]` and `dask[dataframe]`: Core parallelization
- GPU drivers: CUDA toolkit must match `sm_75` capability
- Redis: Optional but integrated - API runs without it (with warnings)

## When Modifying Code

**Adding new forecasting methods**: 
1. Create CUDA kernel in `app/libs/`
2. Compile to `.so` file
3. Add ctypes wrapper in `app/aplicacao.py`
4. Integrate into `forecast_temp()` error comparison

**Changing prediction logic**: 
- Modify `forecast_temp()` in `app/aplicacao.py`
- Respect the train/test split pattern (70/30)
- Always return dict with `final_projection` and `probabilidade_subir` keys

**Adding API endpoints**:
- Use FastAPI in `app/main.py` for new features
- Follow async/await pattern for long-running operations
- Include proper form/query parameter validation

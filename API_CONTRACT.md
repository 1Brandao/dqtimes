# DQTimes API Contract Documentation

**Version:** 1.0.0  
**Last Updated:** November 25, 2025  
**Base URL (FastAPI):** `http://localhost:80`  
**Base URL (Flask):** `http://localhost:5000` (Legacy - Async Job Queue)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [FastAPI Endpoints](#fastapi-endpoints)
5. [Flask Endpoints (Legacy Async)](#flask-endpoints-legacy-async)
6. [Data Models](#data-models)
7. [Error Responses](#error-responses)
8. [Examples](#examples)

---

## Overview

DQTimes is a high-performance time series forecasting API that uses CUDA-accelerated algorithms to predict future values based on historical data. The system provides two API surfaces:

- **FastAPI Service** (Primary): Synchronous predictions with optional pagination for bulk forecasting
- **Flask Service** (Legacy): Asynchronous job queue with Celery for long-running tasks

### Key Features

- CUDA-accelerated forecasting algorithms (Holt-Winters, Moving Averages)
- Automatic algorithm selection based on MSE comparison
- Batch processing with Dask distributed computing
- Redis caching layer
- Probability calculations for trend prediction

---

## Architecture

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| FastAPI Backend | 80 | Main prediction API |
| Dask Dashboard | 8787 | Distributed computing monitoring |
| Redis | 6379 | Caching and session storage |
| Flask API | 5000 | Legacy async job queue |
| Load Balancer | 8000 | TypeScript least-connection load balancer |

### Dependencies

- **Redis**: Required for health checks, optional for caching
- **PostgreSQL**: Required for Flask async job tracking
- **CUDA Libraries**: Pre-compiled `.so` files in `app/libs/`
- **Dask Cluster**: Automatically initialized on FastAPI startup

---

## Authentication

**Current Status:** No authentication required (v1.0.0)

**Future Considerations:** 
- API key authentication
- Rate limiting per client
- OAuth 2.0 for enterprise deployments

---

## FastAPI Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check API and Redis availability status.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:80
```

**Response 200 OK:**
```json
{
  "status": "ok",
  "redis": "connected"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always "ok" if API is running |
| `redis` | string | "connected" or "disconnected" |

**Example cURL:**
```bash
curl http://localhost:80/health
```

---

### 2. List Projection

**Endpoint:** `POST /projecao_lista/`

**Description:** Generate forecasts for a single time series provided as a JSON array.

**Request Headers:**
```
Content-Type: multipart/form-data
```

**Request Body (Form Data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lista_historico` | string (JSON array) | Yes | Historical time series data as JSON string |
| `quantidade_projecoes` | integer | Yes | Number of future points to forecast |

**Example Request:**
```http
POST /projecao_lista/ HTTP/1.1
Host: localhost:80
Content-Type: multipart/form-data

lista_historico=[1.2, 2.5, 3.1, 4.8, 5.3, 6.7, 7.2, 8.9, 9.4, 10.1]
quantidade_projecoes=3
```

**Response 200 OK:**
```json
{
  "projecoes": {
    "final_projection": [
      [10.45, 11.23, 11.87]
    ],
    "moving_averages": [
      [3.27, 4.13, 5.07, 6.20, 7.07, 8.27, 9.17],
      [3.65, 4.55, 5.50, 6.70, 7.55, 8.70],
      [3.94, 4.82, 5.88, 7.04, 7.88],
      [4.18, 5.05, 6.18, 7.30],
      [4.39, 5.26, 6.43],
      [5.74, 6.76],
      [7.11]
    ],
    "holt_winters_projections": [
      [2.89, 3.71, 4.46, 5.82, 6.91, 8.05, 9.12, 10.21],
      [3.12, 4.02, 4.93, 6.15, 7.22, 8.34, 9.43],
      [3.45, 4.41, 5.38, 6.58, 7.64, 8.75],
      [3.67, 4.68, 5.69, 6.88, 7.93],
      [3.88, 4.94, 5.99, 7.17],
      [5.92, 7.23, 8.51],
      [7.45, 8.89]
    ],
    "probabilidade_subir": 0.7234567890123456
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `projecoes.final_projection` | array[array[float]] | Best forecast selected by MSE comparison |
| `projecoes.moving_averages` | array[array[float]] | All moving average forecasts (periods: 3,4,5,6,7,14,30) |
| `projecoes.holt_winters_projections` | array[array[float]] | All Holt-Winters forecasts (periods: 3,4,5,6,7,14,30) |
| `projecoes.probabilidade_subir` | float | Bayesian probability of upward trend (0.0-1.0) |

**Algorithm Details:**

1. Splits data 70% training, 30% testing
2. Tests 7 periods (3, 4, 5, 6, 7, 14, 30) with both algorithms
3. Selects best method based on MSE against test data
4. Applies best method to full dataset for final projection
5. Calculates Bayesian probability using binarized trend analysis

**Example cURL:**
```bash
curl -X POST http://localhost:80/projecao_lista/ \
  -F "lista_historico=[1.2,2.5,3.1,4.8,5.3,6.7,7.2,8.9,9.4,10.1]" \
  -F "quantidade_projecoes=3"
```

**Error Responses:**

- **422 Unprocessable Entity:** Invalid JSON format in `lista_historico`
```json
{
  "detail": [
    {
      "loc": ["body", "lista_historico"],
      "msg": "Invalid JSON format",
      "type": "value_error.jsondecode"
    }
  ]
}
```

---

### 3. DataFrame Projection (Batch Processing)

**Endpoint:** `POST /projecao_dataframe/`

**Description:** Generate forecasts for multiple time series from a CSV file with pagination support.

**Request Headers:**
```
Content-Type: multipart/form-data
```

**Request Body (Form Data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `csv_dataframe` | file | Yes | CSV file containing time series (each row = one series) |
| `quantidade_projecoes` | integer | Yes | Number of future points to forecast per series |
| `header` | boolean | Yes | Whether CSV has header row |
| `index_col` | boolean | Yes | Whether to drop first column (index) |
| `page` | integer | No | Page number (default: 1, min: 1) |
| `page_size` | integer | No | Rows per page (default: 10, min: 1) |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Current page number (≥ 1) |
| `page_size` | integer | 10 | Number of series to process per page (≥ 1) |

**Example CSV Format:**
```csv
series_id,t1,t2,t3,t4,t5,t6,t7,t8,t9,t10
series_1,1.2,2.5,3.1,4.8,5.3,6.7,7.2,8.9,9.4,10.1
series_2,2.1,3.4,4.2,5.8,6.1,7.5,8.3,9.7,10.2,11.4
series_3,0.8,1.9,2.7,3.5,4.2,5.1,5.9,6.8,7.3,8.1
```

**Example Request:**
```http
POST /projecao_dataframe/?page=1&page_size=2 HTTP/1.1
Host: localhost:80
Content-Type: multipart/form-data

csv_dataframe=@timeseries_data.csv
quantidade_projecoes=3
header=true
index_col=true
```

**Response 200 OK:**
```json
{
  "execution_time": 2.3456789,
  "total_pages": 5,
  "current_page": 1,
  "projecoes": [
    {
      "final_projection": [[10.45, 11.23, 11.87]],
      "moving_averages": [
        [3.27, 4.13, 5.07, 6.20, 7.07, 8.27, 9.17],
        [3.65, 4.55, 5.50, 6.70, 7.55, 8.70],
        [3.94, 4.82, 5.88, 7.04, 7.88],
        [4.18, 5.05, 6.18, 7.30],
        [4.39, 5.26, 6.43],
        [5.74, 6.76],
        [7.11]
      ],
      "holt_winters_projections": [
        [2.89, 3.71, 4.46, 5.82, 6.91, 8.05, 9.12, 10.21],
        [3.12, 4.02, 4.93, 6.15, 7.22, 8.34, 9.43],
        [3.45, 4.41, 5.38, 6.58, 7.64, 8.75],
        [3.67, 4.68, 5.69, 6.88, 7.93],
        [3.88, 4.94, 5.99, 7.17],
        [5.92, 7.23, 8.51],
        [7.45, 8.89]
      ],
      "probabilidade_subir": 0.7234567890123456
    },
    {
      "final_projection": [[11.67, 12.34, 13.01]],
      "moving_averages": [
        [4.23, 5.18, 6.12, 7.30, 8.17, 9.37, 10.27],
        [4.61, 5.55, 6.50, 7.70, 8.55, 9.70],
        [4.90, 5.82, 6.88, 8.04, 8.88],
        [5.14, 6.05, 7.18, 8.30],
        [5.35, 6.26, 7.43],
        [6.70, 7.76],
        [8.07]
      ],
      "holt_winters_projections": [
        [3.85, 4.67, 5.42, 6.78, 7.87, 9.01, 10.08, 11.17],
        [4.08, 4.98, 5.89, 7.11, 8.18, 9.30, 10.39],
        [4.41, 5.37, 6.34, 7.54, 8.60, 9.71],
        [4.63, 5.64, 6.65, 7.84, 8.89],
        [4.84, 5.90, 6.95, 8.13],
        [6.88, 8.19, 9.47],
        [8.41, 9.85]
      ],
      "probabilidade_subir": 0.8123456789012345
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `execution_time` | float | Total processing time in seconds |
| `total_pages` | integer | Total number of pages available |
| `current_page` | integer | Current page number |
| `projecoes` | array[object] | Array of forecast results (one per series on page) |

**Processing Details:**

1. CSV loaded with Dask for distributed processing
2. Optional header/index column handling
3. Pagination applied via `ddf.loc[start:end]`
4. Each row processed independently with `forecast_temp()`
5. Results aggregated with execution timing

**Example cURL:**
```bash
curl -X POST "http://localhost:80/projecao_dataframe/?page=1&page_size=10" \
  -F "csv_dataframe=@timeseries_data.csv" \
  -F "quantidade_projecoes=3" \
  -F "header=true" \
  -F "index_col=true"
```

**Error Responses:**

- **404 Not Found:** Page number exceeds total pages
```json
{
  "detail": "Page number out of range"
}
```

- **422 Unprocessable Entity:** Invalid file format or missing required fields
```json
{
  "detail": [
    {
      "loc": ["body", "csv_dataframe"],
      "msg": "Invalid CSV format",
      "type": "value_error"
    }
  ]
}
```

---

## Flask Endpoints (Legacy Async)

### 4. Submit Prediction Job

**Endpoint:** `POST /predict`

**Description:** Submit an async prediction task to Celery queue. Returns immediately with task ID.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload` | object | Yes | Arbitrary JSON payload for prediction task |

**Example Request:**
```http
POST /predict HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "series_data": [1.2, 2.5, 3.1, 4.8, 5.3, 6.7, 7.2, 8.9, 9.4, 10.1],
  "forecast_count": 3,
  "metadata": {
    "source": "sensor_A1",
    "timestamp": "2025-11-25T10:30:00Z"
  }
}
```

**Response 202 Accepted:**
```json
{
  "task_id": "a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d",
  "status": "PENDING"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string (UUID) | Unique identifier for tracking task status |
| `status` | string | Initial status (always "PENDING") |

**Database Record Created:**

When a job is submitted, a record is created in the PostgreSQL `jobs` table:

```sql
INSERT INTO jobs (task_id, status, created_at, payload)
VALUES ('a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d', 'PENDING', '2025-11-25 10:30:00', '{"series_data": [...]}');
```

**Example cURL:**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "series_data": [1.2,2.5,3.1,4.8,5.3,6.7,7.2,8.9,9.4,10.1],
    "forecast_count": 3
  }'
```

---

### 5. Check Job Status

**Endpoint:** `GET /status/<task_id>`

**Description:** Retrieve current status and result of async prediction job.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string (UUID) | Yes | Task identifier from `/predict` response |

**Example Request:**
```http
GET /status/a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d HTTP/1.1
Host: localhost:5000
```

**Response 200 OK (Pending):**
```json
{
  "task_id": "a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d",
  "status": "PENDING",
  "created_at": "2025-11-25T10:30:00.123456",
  "started_at": null,
  "finished_at": null,
  "payload": {
    "series_data": [1.2, 2.5, 3.1, 4.8, 5.3, 6.7, 7.2, 8.9, 9.4, 10.1],
    "forecast_count": 3
  },
  "result": null
}
```

**Response 200 OK (In Progress):**
```json
{
  "task_id": "a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d",
  "status": "IN_PROGRESS",
  "created_at": "2025-11-25T10:30:00.123456",
  "started_at": "2025-11-25T10:30:01.234567",
  "finished_at": null,
  "payload": {
    "series_data": [1.2, 2.5, 3.1, 4.8, 5.3, 6.7, 7.2, 8.9, 9.4, 10.1],
    "forecast_count": 3
  },
  "result": null
}
```

**Response 200 OK (Success):**
```json
{
  "task_id": "a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d",
  "status": "SUCCESS",
  "created_at": "2025-11-25T10:30:00.123456",
  "started_at": "2025-11-25T10:30:01.234567",
  "finished_at": "2025-11-25T10:30:03.345678",
  "payload": {
    "series_data": [1.2, 2.5, 3.1, 4.8, 5.3, 6.7, 7.2, 8.9, 9.4, 10.1],
    "forecast_count": 3
  },
  "result": {
    "payload": {
      "series_data": [1.2, 2.5, 3.1, 4.8, 5.3, 6.7, 7.2, 8.9, 9.4, 10.1],
      "forecast_count": 3
    },
    "processed_at": "2025-11-25T10:30:03.345678"
  }
}
```

**Response 200 OK (Failure):**
```json
{
  "task_id": "a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d",
  "status": "FAILURE",
  "created_at": "2025-11-25T10:30:00.123456",
  "started_at": "2025-11-25T10:30:01.234567",
  "finished_at": "2025-11-25T10:30:02.456789",
  "payload": {
    "series_data": [1.2, 2.5, 3.1],
    "forecast_count": 50
  },
  "result": {
    "error": "Insufficient data points for requested forecast length"
  }
}
```

**Response 404 Not Found:**
```json
{
  "error": "not_found"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string (UUID) | Task identifier |
| `status` | string | "PENDING" \| "IN_PROGRESS" \| "SUCCESS" \| "FAILURE" |
| `created_at` | string (ISO 8601) | Timestamp when task was created |
| `started_at` | string (ISO 8601) \| null | Timestamp when processing began |
| `finished_at` | string (ISO 8601) \| null | Timestamp when processing completed |
| `payload` | object | Original request payload |
| `result` | object \| null | Task result (SUCCESS) or error details (FAILURE) |

**Status Lifecycle:**

```
PENDING → IN_PROGRESS → SUCCESS
                      → FAILURE
```

**Example cURL:**
```bash
curl http://localhost:5000/status/a7b3c8d9-1e2f-4a5b-8c9d-0e1f2a3b4c5d
```

---

## Data Models

### Forecast Result Schema

```typescript
interface ForecastResult {
  final_projection: number[][];        // Best selected forecast
  moving_averages: number[][];         // 7 MA forecasts (periods 3,4,5,6,7,14,30)
  holt_winters_projections: number[][]; // 7 HW forecasts (periods 3,4,5,6,7,14,30)
  probabilidade_subir: number;         // Bayesian probability (0.0-1.0)
}
```

### Job Record Schema (PostgreSQL)

```typescript
interface Job {
  id: number;                    // Auto-increment primary key
  task_id: string;               // UUID, indexed, unique
  status: string;                // "PENDING" | "IN_PROGRESS" | "SUCCESS" | "FAILURE"
  created_at: string;            // ISO 8601 timestamp
  started_at: string | null;     // ISO 8601 timestamp
  finished_at: string | null;    // ISO 8601 timestamp
  payload: object;               // JSONB - original request
  result: object | null;         // JSONB - task output or error
}
```

### Forecast Periods

The system automatically tests these periods for algorithm selection:

```python
periods = [3, 4, 5, 6, 7, 14, 30]
```

Each period represents the window size for:
- **Moving Averages**: Simple arithmetic mean over window
- **Holt-Winters**: Triple exponential smoothing with trend/seasonality

---

## Error Responses

### Standard Error Format (FastAPI)

```json
{
  "detail": "Error message" | [
    {
      "loc": ["path", "to", "field"],
      "msg": "Validation error message",
      "type": "error_type"
    }
  ]
}
```

### HTTP Status Codes

| Code | Description | Example Scenario |
|------|-------------|------------------|
| 200 | OK | Successful request |
| 202 | Accepted | Async job queued |
| 404 | Not Found | Invalid task_id or page out of range |
| 422 | Unprocessable Entity | Invalid JSON, malformed CSV, missing fields |
| 500 | Internal Server Error | CUDA library error, Redis connection failure |
| 503 | Service Unavailable | Dask cluster down, database unreachable |

### Common Error Scenarios

#### Invalid JSON in lista_historico
```json
{
  "detail": [
    {
      "loc": ["body", "lista_historico"],
      "msg": "Expecting value: line 1 column 1 (char 0)",
      "type": "value_error.jsondecode"
    }
  ]
}
```

#### Page Out of Range
```json
{
  "detail": "Page number out of range"
}
```

#### Redis Disconnected (Warning)
```
⚠️ Aviso: Redis não está disponível
```
*Note: API continues to function without Redis*

#### Task Not Found
```json
{
  "error": "not_found"
}
```

---

## Examples

### Example 1: Simple Single Series Forecast

**Request:**
```bash
curl -X POST http://localhost:80/projecao_lista/ \
  -F "lista_historico=[100,105,110,108,115,120,118,125,130,135]" \
  -F "quantidade_projecoes=5"
```

**Response:**
```json
{
  "projecoes": {
    "final_projection": [[138.5, 142.3, 146.1, 149.8, 153.5]],
    "moving_averages": [
      [104.33, 107.67, 111.0, 113.67, 117.67, 121.0, 124.33, 130.0],
      [105.75, 109.25, 112.75, 116.5, 119.75, 124.5],
      [106.6, 110.2, 114.2, 118.4, 122.4],
      [107.17, 111.17, 115.5, 120.0],
      [107.57, 111.86, 116.29],
      [114.29, 120.71],
      [119.29]
    ],
    "holt_winters_projections": [
      [103.2, 106.8, 109.5, 113.8, 118.2, 121.5, 126.3, 131.7, 136.8],
      [104.5, 108.3, 111.2, 115.6, 119.8, 123.9, 129.1],
      [105.3, 109.5, 112.8, 117.3, 121.7, 126.2],
      [106.1, 110.4, 114.1, 118.7, 123.5],
      [106.8, 111.2, 115.3, 120.1],
      [115.8, 121.4, 127.3],
      [120.5, 127.8]
    ],
    "probabilidade_subir": 0.85
  }
}
```

**Interpretation:**
- Best algorithm selected: Moving Average (period 4) based on lowest MSE
- Final forecast: 5 future values starting from 138.5
- 85% probability of upward trend continuation

---

### Example 2: Batch CSV Processing with Pagination

**CSV File (sales_data.csv):**
```csv
store_id,jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec
store_1,1500,1600,1750,1900,2100,2300,2500,2700,2900,3100,3300,3500
store_2,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350
store_3,2200,2150,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200
store_4,1200,1250,1300,1350,1400,1450,1500,1550,1600,1650,1700,1750
store_5,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100
```

**Request (Page 1):**
```bash
curl -X POST "http://localhost:80/projecao_dataframe/?page=1&page_size=2" \
  -F "csv_dataframe=@sales_data.csv" \
  -F "quantidade_projecoes=6" \
  -F "header=true" \
  -F "index_col=true"
```

**Response:**
```json
{
  "execution_time": 1.2345,
  "total_pages": 3,
  "current_page": 1,
  "projecoes": [
    {
      "final_projection": [[3700, 3900, 4100, 4300, 4500, 4700]],
      "moving_averages": [...],
      "holt_winters_projections": [...],
      "probabilidade_subir": 0.92
    },
    {
      "final_projection": [[1400, 1450, 1500, 1550, 1600, 1650]],
      "moving_averages": [...],
      "holt_winters_projections": [...],
      "probabilidade_subir": 0.88
    }
  ]
}
```

**Request (Page 2):**
```bash
curl -X POST "http://localhost:80/projecao_dataframe/?page=2&page_size=2" \
  -F "csv_dataframe=@sales_data.csv" \
  -F "quantidade_projecoes=6" \
  -F "header=true" \
  -F "index_col=true"
```

---

### Example 3: Async Job with Celery (Flask)

**Step 1: Submit Job**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "series_data": [50,55,60,58,65,70,68,75,80,85],
    "forecast_count": 3,
    "metadata": {
      "sensor": "temperature_sensor_01",
      "location": "warehouse_A"
    }
  }'
```

**Response:**
```json
{
  "task_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "PENDING"
}
```

**Step 2: Poll Status (Immediately)**
```bash
curl http://localhost:5000/status/f9e8d7c6-b5a4-3210-9876-543210fedcba
```

**Response:**
```json
{
  "task_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "IN_PROGRESS",
  "created_at": "2025-11-25T15:30:00.123456",
  "started_at": "2025-11-25T15:30:01.234567",
  "finished_at": null,
  "payload": {
    "series_data": [50,55,60,58,65,70,68,75,80,85],
    "forecast_count": 3,
    "metadata": {
      "sensor": "temperature_sensor_01",
      "location": "warehouse_A"
    }
  },
  "result": null
}
```

**Step 3: Poll Status (After Completion)**
```bash
curl http://localhost:5000/status/f9e8d7c6-b5a4-3210-9876-543210fedcba
```

**Response:**
```json
{
  "task_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "SUCCESS",
  "created_at": "2025-11-25T15:30:00.123456",
  "started_at": "2025-11-25T15:30:01.234567",
  "finished_at": "2025-11-25T15:30:03.456789",
  "payload": {
    "series_data": [50,55,60,58,65,70,68,75,80,85],
    "forecast_count": 3,
    "metadata": {
      "sensor": "temperature_sensor_01",
      "location": "warehouse_A"
    }
  },
  "result": {
    "payload": {
      "series_data": [50,55,60,58,65,70,68,75,80,85],
      "forecast_count": 3,
      "metadata": {
        "sensor": "temperature_sensor_01",
        "location": "warehouse_A"
      }
    },
    "processed_at": "2025-11-25T15:30:03.456789"
  }
}
```

---

### Example 4: Python Client Implementation

```python
import requests
import json
import time

class DQTimesClient:
    def __init__(self, base_url="http://localhost:80"):
        self.base_url = base_url
        
    def check_health(self):
        """Check API health status"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def forecast_single(self, time_series, n_forecasts):
        """Generate forecast for single time series"""
        data = {
            "lista_historico": json.dumps(time_series),
            "quantidade_projecoes": n_forecasts
        }
        response = requests.post(f"{self.base_url}/projecao_lista/", data=data)
        response.raise_for_status()
        return response.json()["projecoes"]
    
    def forecast_batch(self, csv_path, n_forecasts, page=1, page_size=10, 
                       has_header=True, has_index=True):
        """Generate forecasts for CSV batch"""
        with open(csv_path, 'rb') as f:
            files = {'csv_dataframe': f}
            data = {
                'quantidade_projecoes': n_forecasts,
                'header': str(has_header).lower(),
                'index_col': str(has_index).lower()
            }
            params = {'page': page, 'page_size': page_size}
            
            response = requests.post(
                f"{self.base_url}/projecao_dataframe/",
                files=files,
                data=data,
                params=params
            )
            response.raise_for_status()
            return response.json()

# Usage
client = DQTimesClient()

# Check health
health = client.check_health()
print(f"API Status: {health['status']}, Redis: {health['redis']}")

# Single forecast
series = [10, 12, 15, 18, 22, 25, 30, 35, 40, 45]
result = client.forecast_single(series, n_forecasts=5)
print(f"Forecast: {result['final_projection']}")
print(f"Probability of increase: {result['probabilidade_subir']:.2%}")

# Batch forecast
batch_result = client.forecast_batch(
    csv_path="sales_data.csv",
    n_forecasts=3,
    page=1,
    page_size=10
)
print(f"Processed in {batch_result['execution_time']:.2f}s")
print(f"Page {batch_result['current_page']} of {batch_result['total_pages']}")
```

---

### Example 5: JavaScript/TypeScript Client

```typescript
interface ForecastResult {
  final_projection: number[][];
  moving_averages: number[][];
  holt_winters_projections: number[][];
  probabilidade_subir: number;
}

interface BatchResult {
  execution_time: number;
  total_pages: number;
  current_page: number;
  projecoes: ForecastResult[];
}

class DQTimesClient {
  constructor(private baseUrl: string = "http://localhost:80") {}

  async checkHealth(): Promise<{ status: string; redis: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async forecastSingle(
    timeSeries: number[],
    nForecasts: number
  ): Promise<ForecastResult> {
    const formData = new FormData();
    formData.append("lista_historico", JSON.stringify(timeSeries));
    formData.append("quantidade_projecoes", nForecasts.toString());

    const response = await fetch(`${this.baseUrl}/projecao_lista/`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.projecoes;
  }

  async forecastBatch(
    csvFile: File,
    nForecasts: number,
    options: {
      page?: number;
      pageSize?: number;
      hasHeader?: boolean;
      hasIndex?: boolean;
    } = {}
  ): Promise<BatchResult> {
    const {
      page = 1,
      pageSize = 10,
      hasHeader = true,
      hasIndex = true,
    } = options;

    const formData = new FormData();
    formData.append("csv_dataframe", csvFile);
    formData.append("quantidade_projecoes", nForecasts.toString());
    formData.append("header", hasHeader.toString());
    formData.append("index_col", hasIndex.toString());

    const url = new URL(`${this.baseUrl}/projecao_dataframe/`);
    url.searchParams.append("page", page.toString());
    url.searchParams.append("page_size", pageSize.toString());

    const response = await fetch(url.toString(), {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}

// Usage
const client = new DQTimesClient();

// Check health
const health = await client.checkHealth();
console.log(`API: ${health.status}, Redis: ${health.redis}`);

// Single forecast
const series = [10, 12, 15, 18, 22, 25, 30, 35, 40, 45];
const forecast = await client.forecastSingle(series, 5);
console.log("Forecast:", forecast.final_projection);
console.log("Probability:", (forecast.probabilidade_subir * 100).toFixed(2) + "%");

// Batch forecast (in browser with file input)
const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
const file = fileInput.files?.[0];
if (file) {
  const batchResult = await client.forecastBatch(file, 3, {
    page: 1,
    pageSize: 10,
  });
  console.log(`Processed ${batchResult.projecoes.length} series`);
  console.log(`Time: ${batchResult.execution_time.toFixed(2)}s`);
}
```

---

## Best Practices

### 1. Choosing Between Endpoints

| Use Case | Recommended Endpoint | Reason |
|----------|---------------------|--------|
| Single series, real-time | `POST /projecao_lista/` | Fast synchronous response |
| Batch processing (<100 series) | `POST /projecao_dataframe/` | Efficient pagination, Dask acceleration |
| Large batch (>1000 series) | `POST /predict` (Flask) | Non-blocking async queue |
| Dashboard monitoring | `GET /health` | Quick status check |

### 2. Data Requirements

- **Minimum data points:** At least 30 points recommended for accurate forecasting
- **Maximum forecasts:** Should not exceed 30% of historical data length
- **Data quality:** Remove outliers and handle missing values before submission
- **Format:** Numeric values only (integers or floats)

### 3. Pagination Strategy

For large CSV files:
```python
# Process all pages
page = 1
all_results = []

while True:
    response = forecast_batch(csv_path, n_forecasts=3, page=page, page_size=50)
    all_results.extend(response['projecoes'])
    
    if page >= response['total_pages']:
        break
    page += 1
```

### 4. Error Handling

```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post(url, data=data)
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 422:
        print(f"Validation error: {e.response.json()['detail']}")
    elif e.response.status_code == 404:
        print("Page not found or task doesn't exist")
    else:
        print(f"HTTP error: {e}")
        
except requests.exceptions.ConnectionError:
    print("Failed to connect to API - check if service is running")
    
except RequestException as e:
    print(f"Request failed: {e}")
```

### 5. Performance Optimization

- **Batch size:** Use `page_size=50-100` for optimal Dask performance
- **Redis caching:** Enable Redis to cache frequent forecast patterns
- **Parallel requests:** For multiple independent series, use ThreadPoolExecutor
- **CSV optimization:** Pre-filter unnecessary columns before upload

---

## Environment Configuration

### Required Environment Variables

#### FastAPI Service (docker-compose.yml)

```yaml
environment:
  DASK_DASHBOARD_ADDRESS: ":8787"
  REDIS_HOST: "redis"
  REDIS_PORT: "6379"
  REDIS_DB: "0"
```

#### Flask Service (optional - not in current docker-compose)

```yaml
environment:
  CELERY_BROKER_URL: "redis://redis:6379/1"
  DATABASE_URL: "postgresql://user:password@postgres:5432/dqtimes"
```

### Service URLs

| Service | Development | Production |
|---------|-------------|------------|
| FastAPI | `http://localhost:80` | `https://api.dqtimes.com` |
| Dask Dashboard | `http://localhost:8787` | Internal only |
| Flask API | `http://localhost:5000` | `https://async.dqtimes.com` |
| Load Balancer | `http://localhost:8000` | `https://lb.dqtimes.com` |

---

## Changelog

### Version 1.0.0 (2025-11-25)

- Initial API contract documentation
- FastAPI endpoints: `/health`, `/projecao_lista/`, `/projecao_dataframe/`
- Flask async endpoints: `/predict`, `/status/<task_id>`
- CUDA-accelerated forecasting algorithms
- Dask distributed processing support
- Redis integration for health monitoring

---

## Support & Resources

### Documentation
- Project README: `dqtimes/README.md`
- Copilot Instructions: `.github/copilot-instructions.md`

### Monitoring
- Dask Dashboard: `http://localhost:8787` - View distributed task execution
- Redis CLI: `docker exec -it dqtimes_redis redis-cli` - Check cache status

### Source Code
- FastAPI Application: `dqtimes/app/main.py`
- Flask Application: `dqtimes/api.py`
- Forecast Logic: `dqtimes/app/aplicacao.py`
- CUDA Libraries: `dqtimes/app/libs/*.so`

### Testing
- Test Script: `dqtimes/teste_request.py`
- Unit Tests: `dqtimes/app/tests/`

---

## License & Attribution

**Project:** DQTimes  
**Repository:** dqtimesFront  
**Organization:** GRUPO-02-4-PERIODO-BIOPARK-2025  
**API Version:** 1.0.0  
**Documentation Date:** November 25, 2025

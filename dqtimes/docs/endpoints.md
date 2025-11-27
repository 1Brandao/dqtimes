

````markdown
# Documentação Técnica da API e Módulos de Previsão

Este documento detalha os endpoints da API FastAPI, bem como as funções internas de processamento (CUDA/Python) e tarefas assíncronas (Celery).

---

## Parte 1: Collection de Endpoints (API)

### 1. Login (Autenticação)
Realiza a autenticação e retorna um token JWT (Bearer) para acesso aos endpoints protegidos.

- **Rota:** `/auth/login`
- **Método:** `POST`
- **Content-Type:** `application/x-www-form-urlencoded`

#### Entrada
| Parâmetro | Tipo | Obrigatório | Descrição |
| :--- | :--- | :---: | :--- |
| `username` | string | Sim | Usuário cadastrado. |
| `password` | string | Sim | Senha do usuário. |

#### Saída (Exemplo)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
````

-----

### Modelo de Previsão: Dummy (Simulação)

Esta seção documenta a lógica do modelo de fallback (`run_prediction_model`), utilizado para testes de integração ou quando os modelos de IA (TensorFlow/Rust) não estão disponíveis.

**Lógica:** O algoritmo identifica o último valor da série temporal fornecida e projeta um crescimento fixo de 5% (fator 1.05) acumulativo para cada período futuro solicitado.

  - **Rota:** `/api/predict` (Utilizando o modelo padrão ou fallback)
  - **Método:** `POST`
  - **Content-Type:** `application/json`

#### Parâmetros de Entrada (JSON Body)

| Parâmetro | Tipo | Obrigatório | Descrição |
| :--- | :--- | :---: | :--- |
| `series` | list[float] | Sim | Lista contendo a série histórica de valores numéricos. |
| `periods` | int | Sim | Número de previsões futuras a serem geradas. |

#### Exemplos de Requisição

**1. Request Válido (Cenário Padrão)**

**Entrada:**
Uma série com valores estáveis e solicitação de 3 previsões.

```json
{
  "series": [100.0, 102.0, 105.0],
  "periods": 3
}
```

**Processamento (Simulação):**

**Lógica de Cálculo:**

1.  **Último valor:** 105.0
2.  **Período 1:** 105.0 \* 1.05 = **110.25**
3.  **Período 2:** 110.25 \* 1.05 = **115.76**
4.  **Período 3:** 115.76 \* 1.05 = **121.55**

**Saída Esperada (Response):**

```json
{
  "input_series_size": 3,
  "predictions": [110.25, 115.76, 121.55]
}
```

**2. Request Válido (Lista Vazia)**

**Entrada:**

```json
{
  "series": [],
  "periods": 5
}
```

**Saída Esperada:**

```json
{
  "predictions": []
}
```

**3. Request Inválido (Erro de Tipo)**

**Entrada:**

```json
{
  "series": [100, "cem", 102],
  "periods": 3
}
```

**Saída de Erro Esperada:**

```json
{
  "detail": [
    {
      "loc": ["body", "series", 1],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

```
```
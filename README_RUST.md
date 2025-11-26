Traduzi o texto para português; segue abaixo a versão traduzida.

# Biblioteca Rust com Bindings para Python (sa_native)

Este repositório contém uma biblioteca Rust (`sa_native`) que fornece funcionalidade de previsão de séries temporais com bindings para Python via PyO3. Esta implementação atende aos requisitos das issues #40 e #41 do repositório FabianoDicheti/dqtimes.

## Visão geral

A biblioteca `sa_native` é um módulo baseado em Rust que pode ser importado e usado a partir do Python. Ela fornece:
- Uma função `predict_static` para previsão mock de séries temporais
- Validação de entrada e tratamento de erros
- Testes unitários abrangentes em Rust
- Testes de integração em Python

## Estrutura do projeto

```
rust/sa_native/
├── Cargo.toml              # Configuração do pacote Rust
├── pyproject.toml          # Metadados do pacote Python
├── src/
│   └── lib.rs             # Código principal da biblioteca com a função predict_static
└── target/                # Artefatos de build (gerados)
    └── wheels/            # Pacotes wheel do Python (gerados)

examples/
└── python_import_test.py  # Exemplos de uso em Python e testes
```

## Requisitos

- **Rust**: 1.56 ou superior (com Cargo)
- **Python**: 3.8 ou superior
- **Maturin**: 0.14 ou superior (para construir wheels Python)

## Construindo a biblioteca

### Opção 1: Build e instalação com Maturin (recomendado)

1. Instale o maturin se ainda não tiver:
   ```bash
   pip install maturin
   ```

2. Construa e gere um pacote wheel:
   ```bash
   cd rust/sa_native
   maturin build --release
   ```

3. Instale o wheel gerado:
   ```bash
   pip install target/wheels/sa_native-*.whl
   ```

### Opção 2: Modo de desenvolvimento (requer virtualenv)

Se estiver trabalhando em um ambiente virtual Python:

```bash
cd rust/sa_native
maturin develop --release
```

Isto instala o pacote em modo editável para desenvolvimento.

## Executando os testes

### Testes unitários em Rust

Execute os testes unitários em Rust para verificar a lógica central:

```bash
cd rust/sa_native
cargo test --lib
```

Isso executará 5 testes unitários cobrindo:
- Entrada válida com saída esperada
- Previsão para um único valor
- Tratamento de erro para dados vazios
- Tratamento de erro para horizon = 0
- Previsão para horizon grande

### Testes de integração em Python

Após construir e instalar a biblioteca, execute os testes de integração em Python:

```bash
python examples/python_import_test.py
```

Isso verifica:
- Funcionalidade de importação do módulo
- Operações básicas de previsão
- Tratamento de erro a partir do Python
- Validação de entrada

## Exemplo de uso

```python
import sa_native

# Prevê 3 valores futuros com base em dados históricos
historical_data = [1.0, 2.0, 3.0, 4.0, 5.0]
horizon = 3
predictions = sa_native.predict_static(historical_data, horizon)
print(predictions)  # Saída: [5.0, 5.0, 5.0]
```

### Documentação da API

#### `predict_static(data: List[float], horizon: int) -> List[float]`

Prevê valores futuros com base em dados históricos usando uma implementação mock simples.

Parâmetros:
- `data`: Dados históricos como uma lista de floats
- `horizon`: Número de valores futuros a prever (deve ser > 0)

Retorna:
- Lista de valores float previstos (atualmente: último valor repetido)

Levanta:
- `ValueError`: Se `data` estiver vazio ou `horizon` for 0

Observação: Esta é uma implementação mock. Em produção, conteria algoritmos reais de forecast.

## GitHub Actions CI/CD

O repositório inclui um workflow do GitHub Actions (`.github/workflows/rust-python.yml`) que:
1. Executa os testes unitários em Rust (`cargo test`)
2. Constrói o pacote Python com maturin
3. Testa a importação Python e funcionalidades básicas

O workflow roda automaticamente em:
- Push para a branch `main`
- Pull requests para a branch `main`

## Fluxo de desenvolvimento

1. Faça alterações em `src/lib.rs`
2. Execute os testes Rust: `cargo test --lib`
3. Construa o pacote: `maturin build --release`
4. Instale localmente: `pip install target/wheels/sa_native-*.whl --force-reinstall`
5. Teste a integração com Python: `python examples/python_import_test.py`
6. Faça commit das alterações e envie para o GitHub

## Detalhes da implementação

### Algoritmo de previsão mock

A implementação atual usa um algoritmo mock simples que repete o último valor dos dados históricos pelo horizonte especificado. Isso é intencional para fins de demonstração.

Exemplo:
- Entrada: `[1.0, 2.0, 3.0]`, Horizon: `5`
- Saída: `[3.0, 3.0, 3.0, 3.0, 3.0]`

### Arquitetura

A biblioteca separa a lógica central dos bindings para Python:
- `predict_static_impl`: Função pura em Rust com o algoritmo central
- `predict_static`: Função empacotada com PyO3 exposta ao Python
- Testes unitários operam sobre `predict_static_impl` para evitar dependência do runtime Python

## Solução de problemas

### Erro de importação no Python

Se aparecer `ImportError: No module named 'sa_native'`:
1. Certifique-se de que construiu a biblioteca: `cd rust/sa_native && maturin build --release`
2. Instale o wheel: `pip install target/wheels/sa_native-*.whl`

### Erro no modo de desenvolvimento do Maturin

Se `maturin develop` falhar com "Couldn't find a virtualenv":
- Crie e ative um ambiente virtual Python, ou
- Use `maturin build` + `pip install <wheel>` como alternativa

### Falha no Cargo test

Se houver erros de linking ao rodar `cargo test`:
- Use `cargo test --lib` em vez de `cargo test`
- Isso evita problemas com o módulo de extensão PyO3 durante os testes

## Referências

- [Documentação do PyO3](https://pyo3.rs/)
- [Documentação do Maturin](https://www.maturin.rs/)
- [Issues #40 e #41 do FabianoDicheti/dqtimes](https://github.com/FabianoDicheti/dqtimes/issues/)

## Licença

Este projeto faz parte do repositório Matheus-Akio1/sa. Veja o repositório principal para informações sobre a licença.
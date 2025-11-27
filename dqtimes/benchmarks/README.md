# Benchmarks Rust <-> Python (inicial)

Este diretório contém um scaffolding inicial para comparar performance entre uma
implementação em Rust e chamadas dessa implementação via Python.

Formato e objetivo
- Gravar tempos de execução para vários tamanhos de entrada.
- Comparar execução Rust pura (criterion) com execução via Python (pyo3 ou ctypes).
- Resultado salvo em `benchmarks/results.csv` com colunas: `mode,size,repeat,elapsed_seconds`.

Conteúdo
- `bench_python.py` — script Python que tenta importar um módulo `rustlib` (pyo3) ou carregar
  `librustlib.so` via ctypes e executa a função `compute` em diferentes tamanhos de input.
- `rustlib/` — exemplo mínimo de crate Rust com `pyo3` e um benchmark `criterion`.

Como usar (resumo rápido)
1. Instale Rust (rustup) e Python (3.8+). Instale `maturin` se for usar pyo3: `pip install maturin`.
2. No diretório `benchmarks/rustlib` rode `maturin develop --release` para expor `rustlib` ao Python
   (ou `cargo build --release` para gerar `target/release/librustlib.so`).
3. Rode `python3 bench_python.py` para gerar `results.csv`.
4. Rode `cargo bench` dentro do crate Rust para obter resultados do Criterion (Rust puro).

Notas
- O crate em `rustlib` é um exemplo mínimo; ajuste a função `compute` para o algoritmo real que
  você deseja medir.

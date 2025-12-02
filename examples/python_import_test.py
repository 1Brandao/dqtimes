#!/usr/bin/env python3
"""
Teste de Importação Python para Biblioteca Rust sa_native

Este script demonstra como compilar e testar a biblioteca sa_native
que fornece funções de previsão de séries temporais baseadas em Rust via bindings Python.

Instruções de Compilação:
    1. Instale o maturin (se ainda não estiver instalado):
       pip install maturin

    2. Compile e instale a biblioteca em modo de desenvolvimento:
       cd rust/sa_native
       maturin develop --release

    3. Execute este script de teste:
       python examples/python_import_test.py

Método Alternativo de Compilação:
    Compile um pacote wheel:
       cd rust/sa_native
       maturin build --release
       pip install target/wheels/sa_native-*.whl
"""

def test_import():
    """Testa a importação básica do módulo sa_native."""
    try:
        import sa_native
        print("✓ Módulo 'sa_native' importado com sucesso")
        return True
    except ImportError as e:
        print(f"✗ Falha ao importar sa_native: {e}")
        print("\nPor favor, compile a biblioteca primeiro:")
        print("  cd rust/sa_native")
        print("  pip install maturin")
        print("  maturin develop --release")
        return False


def test_predict_static():
    """Testa a função predict_static com várias entradas."""
    import sa_native
    
    print("\n--- Testando função predict_static ---")
    
    # Teste 1: Previsão básica
    print("\nTeste 1: Previsão básica")
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    horizon = 3
    result = sa_native.predict_static(data, horizon)
    print(f"Entrada: {data}, Horizonte: {horizon}")
    print(f"Resultado: {result}")
    assert result == [5.0, 5.0, 5.0], f"Esperado [5.0, 5.0, 5.0], obtido {result}"
    print("✓ Teste aprovado")
    
    # Teste 2: Previsão de valor único
    print("\nTeste 2: Previsão de valor único")
    data = [42.0]
    horizon = 2
    result = sa_native.predict_static(data, horizon)
    print(f"Entrada: {data}, Horizonte: {horizon}")
    print(f"Resultado: {result}")
    assert result == [42.0, 42.0], f"Esperado [42.0, 42.0], obtido {result}"
    print("✓ Teste aprovado")
    
    # Teste 3: Horizonte maior
    print("\nTeste 3: Horizonte maior")
    data = [10.0, 20.0, 30.0]
    horizon = 5
    result = sa_native.predict_static(data, horizon)
    print(f"Entrada: {data}, Horizonte: {horizon}")
    print(f"Resultado: {result}")
    assert result == [30.0] * 5, f"Esperado {[30.0] * 5}, obtido {result}"
    print("✓ Teste aprovado")
    
    # Teste 4: Tratamento de erro - dados vazios
    print("\nTeste 4: Tratamento de erro - dados vazios")
    try:
        result = sa_native.predict_static([], 3)
        print("✗ Deveria ter gerado um erro para dados vazios")
        return False
    except ValueError as e:
        print(f"✓ ValueError gerado corretamente: {e}")
    
    # Teste 5: Tratamento de erro - horizonte zero
    print("\nTeste 5: Tratamento de erro - horizonte zero")
    try:
        result = sa_native.predict_static([1.0, 2.0], 0)
        print("✗ Deveria ter gerado um erro para horizonte zero")
        return False
    except ValueError as e:
        print(f"✓ ValueError gerado corretamente: {e}")
    
    return True


def main():
    """Executor principal de testes."""
    print("=" * 60)
    print("sa_native - Teste de Importação e Funcionalidade Python")
    print("=" * 60)
    
    # Teste de importação
    if not test_import():
        return 1
    
    # Teste de funcionalidade
    try:
        if not test_predict_static():
            return 1
    except Exception as e:
        print(f"\n✗ Teste falhou com erro: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("Todos os testes passaram com sucesso! ✓")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

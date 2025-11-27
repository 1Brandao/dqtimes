use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

/// Lógica central de previsão (pode ser testada sem runtime Python)
fn predict_static_impl(data: &[f64], horizon: usize) -> Result<Vec<f64>, String> {
    // Validar entrada
    if data.is_empty() {
        return Err("Os dados de entrada não podem estar vazios".to_string());
    }
    
    if horizon == 0 {
        return Err("O horizonte deve ser maior que 0".to_string());
    }
    
    // Previsão simulada: repete o último valor para o horizonte especificado
    let last_value = data.last().unwrap();
    let predictions = vec![*last_value; horizon];
    
    Ok(predictions)
}

/// Prevê valores futuros com base em dados históricos (implementação simulada).
/// 
/// Esta é uma implementação simulada simples que retorna o último valor repetido
/// para o horizonte especificado. Em um sistema de produção, isso conteria
/// lógica de previsão real.
///
/// # Argumentos
///
/// * `data` - Dados históricos como um vetor de floats
/// * `horizon` - Número de valores futuros a prever
///
/// # Retorna
///
/// Vetor de valores previstos (simulado: repete o último valor)
///
/// # Erros
///
/// Retorna PyValueError se:
/// * os dados estiverem vazios
/// * horizonte for 0
///
/// # Exemplos
///
/// ```python
/// import sa_native
/// # Prevê 3 valores futuros com base em dados históricos
/// result = sa_native.predict_static([1.0, 2.0, 3.0], 3)
/// # Retorna [3.0, 3.0, 3.0] (último valor repetido)
/// ```
#[pyfunction]
fn predict_static(data: Vec<f64>, horizon: usize) -> PyResult<Vec<f64>> {
    predict_static_impl(&data, horizon)
        .map_err(|e| PyValueError::new_err(e))
}

/// Módulo Python para previsão de séries temporais.
/// 
/// Este módulo fornece funções baseadas em Rust para previsão de séries temporais
/// que podem ser chamadas a partir do Python.
#[pymodule]
fn sa_native(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(predict_static, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_predict_static_valid_input() {
        // Teste com entrada válida
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let horizon = 3;
        let result = predict_static_impl(&data, horizon);
        
        assert!(result.is_ok());
        let predictions = result.unwrap();
        assert_eq!(predictions.len(), 3);
        assert_eq!(predictions, vec![5.0, 5.0, 5.0]);
    }

    #[test]
    fn test_predict_static_single_value() {
        // Teste com valor único
        let data = vec![42.0];
        let horizon = 5;
        let result = predict_static_impl(&data, horizon);
        
        assert!(result.is_ok());
        let predictions = result.unwrap();
        assert_eq!(predictions.len(), 5);
        assert_eq!(predictions, vec![42.0, 42.0, 42.0, 42.0, 42.0]);
    }

    #[test]
    fn test_predict_static_empty_data() {
        // Teste com dados vazios - deve retornar erro
        let data = vec![];
        let horizon = 3;
        let result = predict_static_impl(&data, horizon);
        
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Os dados de entrada não podem estar vazios");
    }

    #[test]
    fn test_predict_static_zero_horizon() {
        // Teste com horizonte zero - deve retornar erro
        let data = vec![1.0, 2.0, 3.0];
        let horizon = 0;
        let result = predict_static_impl(&data, horizon);
        
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "O horizonte deve ser maior que 0");
    }

    #[test]
    fn test_predict_static_large_horizon() {
        // Teste com horizonte grande
        let data = vec![10.0, 20.0, 30.0];
        let horizon = 100;
        let result = predict_static_impl(&data, horizon);
        
        assert!(result.is_ok());
        let predictions = result.unwrap();
        assert_eq!(predictions.len(), 100);
        // Todos os valores devem ser 30.0 (último valor)
        assert!(predictions.iter().all(|&x| x == 30.0));
    }
}

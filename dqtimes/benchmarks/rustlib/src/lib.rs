use pyo3::prelude::*;

/// Função de exemplo `compute` — substitua pelo algoritmo a ser medido.
#[pyfunction]
fn compute(data: Vec<f32>) -> PyResult<f64> {
    let s: f64 = data.iter().map(|v| *v as f64).sum();
    Ok(s)
}

#[pymodule]
fn rustlib(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute, m)?)?;
    Ok(())
}

// Para permitir uso direto em benchs Rust (crate interno) declaramos uma função pública C
#[no_mangle]
pub extern "C" fn compute_c(ptr: *const f32, len: usize) -> f64 {
    if ptr.is_null() || len == 0 { return 0.0; }
    let slice = unsafe { std::slice::from_raw_parts(ptr, len) };
    slice.iter().map(|v| *v as f64).sum()
}

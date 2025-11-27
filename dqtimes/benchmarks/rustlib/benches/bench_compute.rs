use criterion::{criterion_group, criterion_main, Criterion};

// Crie um módulo `src/lib.rs` com uma função pública `compute_c` para testes C-compatible,
// este bench usa essa função via FFI para medir apenas o algoritmo (sem overhead Python).
extern "C" {
    fn compute_c(ptr: *const f32, len: usize) -> f64;
}

fn bench_compute(c: &mut Criterion) {
    let n = 100_000usize;
    let data: Vec<f32> = (0..n).map(|i| i as f32).collect();

    c.bench_function("compute_100k", |b| {
        b.iter(|| unsafe { let _ = compute_c(data.as_ptr(), data.len()); })
    });
}

criterion_group!(benches, bench_compute);
criterion_main!(benches);

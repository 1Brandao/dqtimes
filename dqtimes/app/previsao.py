def run_prediction_model(series: list, periods: int) -> list:
    """
    Simula a execução do modelo de IA (Python ou Wrapper de Rust).
    Aqui entraria a importação do TensorFlow, Torch ou da lib Rust.
    """
    if not series:
        return []
    
    #Logica Dummy (Simula de calculo complexo)
    #Pega a média dos últimos valores e projeta leve crescimento
    growth_factor = 1.05
    last_val = series[-1]
    
    predictions = []
    for _ in range(periods):
        next_val = last_val * growth_factor
        predictions.append(round(next_val, 2))
        last_val = next_val
        
    return predictions
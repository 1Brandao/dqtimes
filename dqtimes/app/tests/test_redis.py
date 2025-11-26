from app.redis_client import get_redis_client, validate_redis_connection

def test_redis_connection():
    """Testa conexão básica com Redis"""
    print("\n🧪 Testando conexão com Redis...")
    
    if not validate_redis_connection():
        print("❌ Falha na conexão")
        return False
    
    client = get_redis_client()
    
    # Teste 1: SET/GET
    print("\n1️⃣  Testando SET/GET...")
    client.set("test_key", "test_value")
    value = client.get("test_key")
    assert value == "test_value", "Falha em SET/GET"
    print("✅ SET/GET funcionando")
    
    # Teste 2: Expiração
    print("\n2️⃣  Testando expiração...")
    client.setex("temp_key", 10, "temporary_value")
    ttl = client.ttl("temp_key")
    assert ttl > 0, "TTL não configurado"
    print(f"✅ Expiração funcionando (TTL: {ttl}s)")
    
    # Teste 3: Listas
    print("\n3️⃣  Testando Listas...")
    client.delete("test_list")
    client.rpush("test_list", "item1", "item2", "item3")
    items = client.lrange("test_list", 0, -1)
    assert len(items) == 3, "Falha em RPUSH/LRANGE"
    print(f"✅ Listas funcionando: {items}")
    
    # Limpeza
    client.delete("test_key", "temp_key", "test_list")
    print("\n✨ Todos os testes passaram!")
    return True

if __name__ == "__main__":
    test_redis_connection()
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()


def start_worker():
    worker_command = [
        "celery",
        "-A", "app.celery_config",
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--queues=forecasts",
        "--hostname=worker@%h"
    ]
    
    print("Iniciando Celery Worker...")
    print(f"Comando: {' '.join(worker_command)}")
    
    try:
        subprocess.run(worker_command, check=True)
    except KeyboardInterrupt:
        print("\nWorker interrompido pelo usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Erro ao iniciar worker: {e}")
        sys.exit(1)


def start_flower():
    flower_command = [
        "celery",
        "-A", "app.celery_config",
        "flower",
        "--port=5555",
        "--broker_api=redis://localhost:6379/0"
    ]
    
    print("Iniciando Flower...")
    print(f"Comando: {' '.join(flower_command)}")
    print("Acesse o dashboard em: http://localhost:5555")
    
    try:
        subprocess.run(flower_command, check=True)
    except KeyboardInterrupt:
        print("\nFlower interrompido pelo usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Erro ao iniciar Flower: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Uso: python worker.py [worker|flower]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "worker":
        start_worker()
    elif command == "flower":
        start_flower()
    else:
        print(f"Comando desconhecido: {command}")
        print("Use: python worker.py [worker|flower]")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script de teste para o fluxo completo do RPA
Testa: Upload → MongoDB → Worker → RPA → Storage

Uso:
    python test_flow.py
"""
import requests
import time
import sys
import os
from datetime import datetime

# Configurações
API_URL = "http://localhost:8000"
PLANILHA_PATH = "example_processos.csv"
CLIENT_NAME = "teste_cogna"


def print_header(message):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)


def print_step(step, message):
    """Imprime passo do teste"""
    print(f"\n[PASSO {step}] {message}")


def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"✅ {message}")


def print_error(message):
    """Imprime mensagem de erro"""
    print(f"❌ {message}")


def print_info(message):
    """Imprime informação"""
    print(f"ℹ️  {message}")


def check_api_running():
    """Verifica se a API está rodando"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException:
        return False


def upload_planilha(planilha_path, client_name):
    """Faz upload da planilha"""
    try:
        with open(planilha_path, 'rb') as f:
            files = {'file': (os.path.basename(planilha_path), f, 'text/csv')}
            response = requests.post(
                f"{API_URL}/tasks/upload/{client_name}",
                files=files,
                timeout=30
            )

        if response.status_code == 201:
            data = response.json()
            print_success(f"Upload realizado com sucesso!")
            print_info(f"Tarefas criadas: {data['tasks_created']}")
            print_info(f"Cliente: {data['client_name']}")
            return data['tasks_created']
        else:
            print_error(f"Erro no upload: {response.status_code}")
            print_error(response.text)
            return 0

    except Exception as e:
        print_error(f"Erro ao fazer upload: {e}")
        return 0


def listar_tarefas_pendentes():
    """Lista tarefas com status pending"""
    try:
        response = requests.get(
            f"{API_URL}/tasks/",
            params={"status_filter": "pending", "limit": 100},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return data['tasks']
        else:
            print_error(f"Erro ao listar tarefas: {response.status_code}")
            return []

    except Exception as e:
        print_error(f"Erro ao listar tarefas: {e}")
        return []


def disparar_processamento():
    """Dispara o processamento manual das tarefas pendentes"""
    try:
        response = requests.post(
            f"{API_URL}/tasks/process-pending",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Processamento disparado!")
            print_info(data['message'])
            return True
        else:
            print_error(f"Erro ao disparar processamento: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Erro ao disparar processamento: {e}")
        return False


def verificar_status_tarefa(process_number):
    """Verifica o status de uma tarefa específica"""
    try:
        response = requests.get(
            f"{API_URL}/tasks/status/{process_number}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None

    except Exception as e:
        print_error(f"Erro ao verificar status: {e}")
        return None


def aguardar_processamento(tarefas, timeout=300):
    """
    Aguarda o processamento das tarefas

    Args:
        tarefas: Lista de tarefas para monitorar
        timeout: Tempo máximo de espera em segundos
    """
    print_info(f"Aguardando processamento (timeout: {timeout}s)...")

    inicio = time.time()
    tarefas_pendentes = {t['process_number']: t for t in tarefas}

    while tarefas_pendentes and (time.time() - inicio) < timeout:
        time.sleep(5)  # Verifica a cada 5 segundos

        for process_number in list(tarefas_pendentes.keys()):
            status_data = verificar_status_tarefa(process_number)

            if status_data:
                status = status_data['status']
                print(f"  • {process_number}: {status}")

                if status in ['completed', 'failed']:
                    tarefa = tarefas_pendentes.pop(process_number)

                    if status == 'completed':
                        print_success(f"Tarefa {process_number} concluída!")
                        if status_data.get('file_path'):
                            print_info(f"  Arquivo: {status_data['file_path']}")
                    else:
                        print_error(f"Tarefa {process_number} falhou!")

    if tarefas_pendentes:
        print_error(f"Timeout! {len(tarefas_pendentes)} tarefas ainda pendentes")
        return False

    return True


def main():
    """Execução principal do teste"""
    print_header("TESTE COMPLETO DO FLUXO RPA")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # PASSO 1: Verificar se API está rodando
    print_step(1, "Verificando se a API está rodando")
    if not check_api_running():
        print_error("API não está rodando!")
        print_info("Inicie a API com: python main.py")
        sys.exit(1)
    print_success("API está rodando")

    # PASSO 2: Verificar se planilha existe
    print_step(2, f"Verificando se planilha existe: {PLANILHA_PATH}")
    if not os.path.exists(PLANILHA_PATH):
        print_error(f"Planilha não encontrada: {PLANILHA_PATH}")
        sys.exit(1)
    print_success(f"Planilha encontrada: {PLANILHA_PATH}")

    # PASSO 3: Fazer upload da planilha
    print_step(3, f"Fazendo upload da planilha para cliente '{CLIENT_NAME}'")
    tarefas_criadas = upload_planilha(PLANILHA_PATH, CLIENT_NAME)

    if tarefas_criadas == 0:
        print_error("Nenhuma tarefa foi criada!")
        sys.exit(1)

    # PASSO 4: Listar tarefas pendentes
    print_step(4, "Listando tarefas pendentes")
    tarefas = listar_tarefas_pendentes()

    if not tarefas:
        print_error("Nenhuma tarefa pendente encontrada!")
        sys.exit(1)

    print_success(f"Encontradas {len(tarefas)} tarefas pendentes:")
    for tarefa in tarefas[:5]:  # Mostra apenas as 5 primeiras
        print(f"  • {tarefa['process_number']} ({tarefa['client_name']})")
    if len(tarefas) > 5:
        print(f"  ... e mais {len(tarefas) - 5} tarefas")

    # PASSO 5: Disparar processamento
    print_step(5, "Disparando processamento manual")
    if not disparar_processamento():
        print_error("Falha ao disparar processamento!")
        sys.exit(1)

    print_info("Worker deve estar rodando para processar as tarefas!")
    print_info("Comando: celery -A worker worker --beat --loglevel=info --pool=solo")

    # PASSO 6: Aguardar processamento
    print_step(6, "Aguardando processamento das tarefas")
    sucesso = aguardar_processamento(tarefas, timeout=300)

    # RESULTADO FINAL
    print_header("RESULTADO DO TESTE")

    if sucesso:
        print_success("TESTE CONCLUÍDO COM SUCESSO! 🎉")
        print_info(f"Todas as {len(tarefas)} tarefas foram processadas")
        print_info(f"Verifique os arquivos em: downloads/{CLIENT_NAME}/")
    else:
        print_error("TESTE FALHOU!")
        print_info("Verifique os logs do worker para detalhes")

    return 0 if sucesso else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

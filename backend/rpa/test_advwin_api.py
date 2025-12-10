#!/usr/bin/env python
"""
Script de teste para integração com ADVWin API
Testa autenticação e upload de documentos GED

Autor: AutoDev
Data: 2025
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sistemas.advwin.advwin_api import ADVWinAPI

# Configuração de logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(
    log_dir, f"test_advwin_api_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def test_autenticacao():
    """Testa a autenticação na API ADVWin"""
    logger.info("=" * 80)
    logger.info("TESTE 1 - AUTENTICAÇÃO NA API ADVWIN")
    logger.info("=" * 80)

    try:
        # Inicializa o cliente (credenciais virão do .env)
        api = ADVWinAPI()

        # Tenta fazer login
        logger.info("Tentando autenticar...")
        sucesso = api.login()

        if sucesso:
            logger.info("=" * 80)
            logger.info("✓ SUCESSO - Autenticação realizada com sucesso!")
            logger.info(f"✓ Token obtido: {api.token[:20]}..." if api.token else "Token não disponível")
            logger.info("=" * 80)
            return True, api
        else:
            logger.error("=" * 80)
            logger.error("✗ FALHA - Erro ao realizar autenticação!")
            logger.error("=" * 80)
            return False, None

    except ValueError as e:
        logger.error("=" * 80)
        logger.error(f"✗ ERRO - Problema com credenciais: {e}")
        logger.error("=" * 80)
        logger.error("DICA: Verifique se o arquivo .env contém:")
        logger.error("      ADVWIN_HOST=https://lfeigelson.twtinfo.com.br")
        logger.error("      ADVWIN_USER=leo_api")
        logger.error("      ADVWIN_PASSWORD=lf@FluxLaw#2025")
        return False, None

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"✗ ERRO durante execução: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return False, None


def test_upload_ged(api: ADVWinAPI):
    """
    Testa o upload de um documento GED

    IMPORTANTE: Este teste requer um arquivo de exemplo.
    Certifique-se de ter um arquivo PDF na pasta temp_downloads/
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TESTE 2 - UPLOAD DE DOCUMENTO GED")
    logger.info("=" * 80)

    try:
        # Procura um arquivo de teste na pasta temp_downloads
        temp_downloads = Path(BASE_DIR) / "temp_downloads"

        if not temp_downloads.exists():
            logger.warning("Pasta temp_downloads não existe. Criando...")
            temp_downloads.mkdir(parents=True, exist_ok=True)
            logger.error("=" * 80)
            logger.error("✗ TESTE IGNORADO - Nenhum arquivo encontrado para upload")
            logger.error("=" * 80)
            logger.error("DICA: Execute um dos RPAs primeiro para baixar documentos,")
            logger.error("      ou coloque manualmente um arquivo PDF na pasta temp_downloads/")
            return False

        # Procura por arquivos PDF
        arquivos_pdf = list(temp_downloads.glob("*.pdf"))

        if not arquivos_pdf:
            logger.error("=" * 80)
            logger.error("✗ TESTE IGNORADO - Nenhum arquivo PDF encontrado em temp_downloads/")
            logger.error("=" * 80)
            logger.error("DICA: Execute um dos RPAs primeiro para baixar documentos,")
            logger.error("      ou coloque manualmente um arquivo PDF na pasta temp_downloads/")
            return False

        # Usa o primeiro arquivo encontrado
        arquivo_teste = str(arquivos_pdf[0])
        nome_arquivo = arquivos_pdf[0].name

        logger.info(f"Arquivo de teste selecionado: {nome_arquivo}")
        logger.info("")

        # Parâmetros de teste para envio
        # AJUSTE ESTES PARÂMETROS CONFORME NECESSÁRIO:
        tabela_or = "Pastas"  # Opções: Pastas, Agenda, Debite, Clientes
        codigo_or = "00016-000407"  # Código de referência (ajuste conforme seu caso)
        descricao = f"Teste de upload via API - {nome_arquivo}"
        observacao = f"Documento enviado automaticamente pelo RPA FluxLaw em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

        logger.info("Parâmetros do upload:")
        logger.info(f"  - Tabela: {tabela_or}")
        logger.info(f"  - Código: {codigo_or}")
        logger.info(f"  - Descrição: {descricao}")
        logger.info("")

        # Pergunta se deseja prosseguir
        print("=" * 80)
        print("ATENÇÃO: Este teste irá enviar um documento REAL para o ADVWin!")
        print(f"Arquivo: {nome_arquivo}")
        print(f"Tabela: {tabela_or}")
        print(f"Código: {codigo_or}")
        print("=" * 80)
        resposta = input("Deseja prosseguir com o upload? (s/N): ").strip().lower()

        if resposta != 's':
            logger.info("Upload cancelado pelo usuário")
            return False

        logger.info("")
        logger.info("Iniciando upload...")

        # Executa o upload
        resultado = api.upload_ged(
            file_path=arquivo_teste,
            tabela_or=tabela_or,
            codigo_or=codigo_or,
            descricao=descricao,
            observacao=observacao
        )

        if resultado.get("sucesso"):
            logger.info("=" * 80)
            logger.info("✓ SUCESSO - Documento enviado com sucesso!")
            logger.info("=" * 80)
            logger.info(f"Status Code: {resultado.get('status_code')}")
            logger.info(f"Resposta: {resultado.get('dados')}")
            logger.info("=" * 80)
            return True
        else:
            logger.error("=" * 80)
            logger.error("✗ FALHA - Erro ao enviar documento!")
            logger.error("=" * 80)
            logger.error(f"Erro: {resultado.get('erro')}")
            if resultado.get('detalhes'):
                logger.error(f"Detalhes: {resultado.get('detalhes')}")
            logger.error("=" * 80)
            return False

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"✗ ERRO durante execução do teste de upload: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return False


def test_upload_multiplos(api: ADVWinAPI):
    """
    Testa o upload de múltiplos documentos GED
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TESTE 3 - UPLOAD DE MÚLTIPLOS DOCUMENTOS GED")
    logger.info("=" * 80)

    try:
        # Procura arquivos na pasta temp_downloads
        temp_downloads = Path(BASE_DIR) / "temp_downloads"

        if not temp_downloads.exists():
            logger.error("=" * 80)
            logger.error("✗ TESTE IGNORADO - Pasta temp_downloads não existe")
            logger.error("=" * 80)
            return False

        # Procura por arquivos PDF
        arquivos_pdf = list(temp_downloads.glob("*.pdf"))

        if len(arquivos_pdf) < 2:
            logger.warning("=" * 80)
            logger.warning("✗ TESTE IGNORADO - Menos de 2 arquivos PDF encontrados")
            logger.warning("=" * 80)
            logger.warning(f"Encontrados: {len(arquivos_pdf)} arquivo(s)")
            logger.warning("DICA: Execute os RPAs primeiro para ter múltiplos arquivos")
            return False

        # Limita a 3 arquivos para o teste
        arquivos_teste = arquivos_pdf[:3]

        logger.info(f"Arquivos selecionados para teste: {len(arquivos_teste)}")
        for arq in arquivos_teste:
            logger.info(f"  - {arq.name}")
        logger.info("")

        # Pergunta se deseja prosseguir
        print("=" * 80)
        print("ATENÇÃO: Este teste irá enviar MÚLTIPLOS documentos para o ADVWin!")
        print(f"Quantidade: {len(arquivos_teste)} arquivo(s)")
        print("=" * 80)
        resposta = input("Deseja prosseguir com o upload? (s/N): ").strip().lower()

        if resposta != 's':
            logger.info("Upload cancelado pelo usuário")
            return False

        # Prepara a lista de arquivos
        lista_arquivos = []
        for arq in arquivos_teste:
            lista_arquivos.append({
                "caminho": str(arq),
                "descricao": f"Upload múltiplo - {arq.name}",
                "observacao": f"Enviado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            })

        logger.info("")
        logger.info("Iniciando upload múltiplo...")

        # Executa o upload múltiplo
        resultado = api.upload_multiplos_ged(
            arquivos=lista_arquivos,
            tabela_or="Pastas",
            codigo_or="123456"
        )

        logger.info("=" * 80)
        logger.info("RESULTADO DO UPLOAD MÚLTIPLO")
        logger.info("=" * 80)
        logger.info(f"Total: {resultado['total']}")
        logger.info(f"✓ Sucesso: {resultado['sucesso']}")
        logger.info(f"✗ Falha: {resultado['falha']}")
        logger.info("=" * 80)

        if resultado["sucesso"] > 0:
            return True
        else:
            return False

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"✗ ERRO durante execução do teste de upload múltiplo: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("")
    logger.info("#" * 80)
    logger.info("# SUITE DE TESTES - ADVWIN API")
    logger.info("#" * 80)
    logger.info("")

    # Teste 1: Autenticação
    sucesso_auth, api = test_autenticacao()

    if not sucesso_auth:
        logger.error("")
        logger.error("#" * 80)
        logger.error("# RESULTADO FINAL: FALHA NA AUTENTICAÇÃO - TESTES INTERROMPIDOS")
        logger.error("#" * 80)
        logger.error("")
        sys.exit(1)

    # Teste 2: Upload único
    logger.info("\nPressione Enter para continuar com o teste de upload...")
    input()

    sucesso_upload = test_upload_ged(api)

    # Teste 3: Upload múltiplo (opcional)
    logger.info("\nPressione Enter para continuar com o teste de upload múltiplo...")
    resposta = input("Ou digite 'pular' para pular este teste: ").strip().lower()

    if resposta != 'pular':
        sucesso_multiplo = test_upload_multiplos(api)
    else:
        sucesso_multiplo = None
        logger.info("Teste de upload múltiplo pulado")

    # Resultado final
    logger.info("")
    logger.info("#" * 80)

    if sucesso_auth and sucesso_upload:
        logger.info("# RESULTADO FINAL: TODOS OS TESTES PRINCIPAIS PASSARAM!")
    elif sucesso_auth:
        logger.info("# RESULTADO FINAL: AUTENTICAÇÃO OK, MAS UPLOAD FALHOU")
    else:
        logger.info("# RESULTADO FINAL: ALGUNS TESTES FALHARAM")

    logger.info("#" * 80)
    logger.info("")

    sys.exit(0 if (sucesso_auth and sucesso_upload) else 1)

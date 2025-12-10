#!/usr/bin/env python
"""
Teste RÁPIDO: Lexxy SuperSim → ADVWin GED
Versão simplificada para testes rápidos

USO:
    python test_quick_supersim_ged.py

Autor: AutoDev
Data: 2025
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sistemas.lexxy.supersim import LexxySuperSim
from sistemas.advwin import get_ged_helper

# ============================================
# CONFIGURAÇÃO - ALTERE AQUI SE NECESSÁRIO
# ============================================
NUMERO_PROCESSO = "5013062-24.2025.8.21.5001"
TABELA_GED = "Pastas"  # Pastas | Agenda | Debite | Clientes
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads_teste")
# ============================================

os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def criar_driver():
    """Cria driver Chrome"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOADS_DIR,
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.automatic_downloads": 1
    })
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    return driver


def main():
    print("\n" + "=" * 80)
    print(f"  TESTE RÁPIDO: SuperSim → GED")
    print("=" * 80)
    print(f"  Processo: {NUMERO_PROCESSO}")
    print(f"  Tabela GED: {TABELA_GED}")
    print("=" * 80 + "\n")

    driver = None

    try:
        # ETAPA 1: Download SuperSim
        print("► ETAPA 1: Baixando documentos do SuperSim...")

        driver = criar_driver()
        supersim = LexxySuperSim(driver=driver, downloads_dir=DOWNLOADS_DIR)

        print("  • Acessando sistema...")
        supersim.ENTRAR_NO_SISTEMA()

        print("  • Fazendo login...")
        if not supersim.LOGIN():
            raise Exception("Erro ao fazer login")

        print("  ✓ Login realizado")

        documentos = supersim.baixa_documento_anexo(NUMERO_PROCESSO)

        if not documentos:
            raise Exception("Nenhum documento baixado")

        print(f"  ✓ {len(documentos)} documento(s) baixado(s)")

        for idx, doc in enumerate(documentos, start=1):
            print(f"    [{idx}] {doc['nome_arquivo_final']}")

        # ETAPA 2: Envio para GED
        print("\n► ETAPA 2: Enviando para ADVWin GED...")

        resposta = input("\n  Confirma envio para GED? (s/N): ").strip().lower()
        if resposta != 's':
            print("  ✗ Envio cancelado")
            return False

        ged_helper = get_ged_helper()

        # IMPORTANTE: Parâmetros corretos conforme ADVWin
        # - codigo_or = código da pasta no ADVWin (ex: "00016-000407")
        # - id_or = número do processo (ex: "5013062-24.2025.8.21.5001")
        resultado = ged_helper.enviar_documentos_ged(
            documentos=documentos,
            numero_processo=NUMERO_PROCESSO,
            tabela_or=TABELA_GED,
            codigo_or="00016-000407",                    # ← CÓDIGO DA PASTA NO ADVWIN
            id_or=NUMERO_PROCESSO                        # ← NÚMERO DO PROCESSO
        )

        print(f"\n  ✓ Envio concluído:")
        print(f"    • Total: {resultado['total']}")
        print(f"    • Sucesso: {resultado['sucesso']}")
        print(f"    • Falhas: {resultado['falha']}")

        # RESULTADO
        print("\n" + "=" * 80)
        if resultado['sucesso'] > 0:
            print("  ✓ TESTE CONCLUÍDO COM SUCESSO!")
        else:
            print("  ✗ TESTE FALHOU - Nenhum documento enviado")
        print("=" * 80 + "\n")

        return resultado['sucesso'] > 0

    except Exception as e:
        print(f"\n✗ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)

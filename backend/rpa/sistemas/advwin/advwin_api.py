"""
Cliente para integração com a API do ADVWin
Responsável por autenticação e envio de documentos (GED)

Autor: AutoDev
Data: 2025
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ADVWinAPI:
    """
    Cliente para interação com a API do ADVWin

    Funcionalidades:
    - Autenticação via login/senha
    - Upload de documentos GED
    """

    def __init__(
        self,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Inicializa o cliente ADVWin API

        Args:
            host: URL base da API (ex: https://lfeigelson.twtinfo.com.br)
            user: Usuário para autenticação
            password: Senha para autenticação
        """
        self.host = host or os.getenv('ADVWIN_HOST')
        self.user = user or os.getenv('ADVWIN_USER')
        self.password = password or os.getenv('ADVWIN_PASSWORD')

        if not self.host:
            raise ValueError(
                "Host da API ADVWin não configurado! "
                "Configure ADVWIN_HOST no .env ou passe como parâmetro"
            )

        if not self.user or not self.password:
            raise ValueError(
                "Credenciais ADVWin não configuradas! "
                "Configure ADVWIN_USER e ADVWIN_PASSWORD no .env ou passe como parâmetros"
            )

        # Remove barra final da URL se existir
        self.host = self.host.rstrip('/')

        # Token de autenticação (será preenchido após login)
        self.token: Optional[str] = None

        # Session para reutilizar conexões
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FluxLaw-RPA/1.0'
        })

        # Desabilita verificação SSL (comum em ambientes de desenvolvimento/staging)
        # IMPORTANTE: Em produção, considere usar certificados válidos
        self.session.verify = False

        # Suprime avisos de SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.info(f"Cliente ADVWin API inicializado - Host: {self.host}, User: {self.user}")
        logger.warning("Verificação SSL desabilitada - use apenas em desenvolvimento")


    def login(self) -> bool:
        """
        Realiza autenticação na API ADVWin

        Returns:
            bool: True se login bem-sucedido, False caso contrário
        """
        try:
            logger.info("Iniciando autenticação na API ADVWin...")

            url = f"{self.host}/api/partner/login"

            payload = {
                "user": self.user,
                "password": self.password  # Campo correto: "password" não "pass"
            }

            logger.info(f"POST {url}")
            logger.info(f"Payload: {{'user': '{self.user}', 'password': '***'}}")

            response = self.session.post(url, json=payload, timeout=30)

            logger.info(f"Status Code: {response.status_code}")
            logger.debug(f"Response: {response.text[:200]}")

            if response.status_code == 200:
                # Remove UTF-8 BOM se presente
                response.encoding = 'utf-8-sig'

                try:
                    data = response.json()
                except Exception as json_error:
                    # Tenta decodificar manualmente removendo BOM
                    logger.warning(f"Erro ao fazer parse do JSON: {json_error}")
                    logger.info("Tentando remover BOM manualmente...")

                    import json
                    text = response.content.decode('utf-8-sig')
                    data = json.loads(text)

                # Tenta obter o token da resposta
                # Formatos comuns: {"token": "..."}, {"access_token": "..."}, {"data": {"token": "..."}}
                if isinstance(data, dict):
                    self.token = (
                        data.get('token') or
                        data.get('access_token') or
                        data.get('data', {}).get('token')
                    )

                    if self.token:
                        # Adiciona o token ao header padrão da sessão
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.token}'
                        })
                        logger.info("✓ Autenticação realizada com sucesso!")
                        return True
                    else:
                        logger.error(f"Token não encontrado na resposta: {data}")
                        return False
                else:
                    logger.error(f"Formato de resposta inesperado: {data}")
                    return False

            else:
                logger.error(
                    f"Erro na autenticação - Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.error("Timeout ao tentar autenticar na API ADVWin")
            return False

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão ao tentar autenticar na API ADVWin: {e}")
            return False

        except Exception as e:
            logger.error(f"Erro inesperado durante autenticação: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


    def upload_ged(
        self,
        file_path: str,
        tabela_or: str,
        codigo_or: str,
        descricao: str,
        id_or: Optional[str] = None,
        observacao: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia um arquivo de GED para o ADVWin

        Args:
            file_path: Caminho completo do arquivo a ser enviado
            tabela_or: Tabela de origem (Pastas, Agenda, Debite, Clientes)
            codigo_or: Código de referência (codigo_comp para pastas, ident para agenda,
                       numero para debite, codigo para cliente)
            descricao: Descrição do arquivo (máximo 250 caracteres)
            id_or: ID para movimentação (opcional)
            observacao: Observações do arquivo (opcional, sem limite)

        Returns:
            dict: Resposta da API contendo status e informações do upload
        """
        if not self.token:
            logger.warning("Token não encontrado. Realizando login automático...")
            if not self.login():
                return {
                    "sucesso": False,
                    "erro": "Falha na autenticação. Não foi possível fazer login."
                }

        try:
            # Valida se o arquivo existe
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                return {
                    "sucesso": False,
                    "erro": f"Arquivo não encontrado: {file_path}"
                }

            if not file_path_obj.is_file():
                logger.error(f"Caminho não é um arquivo: {file_path}")
                return {
                    "sucesso": False,
                    "erro": f"Caminho não é um arquivo: {file_path}"
                }

            # Valida parâmetros obrigatórios
            if not tabela_or:
                return {"sucesso": False, "erro": "Parâmetro 'tabela_or' é obrigatório"}

            if not codigo_or:
                return {"sucesso": False, "erro": "Parâmetro 'codigo_or' é obrigatório"}

            if not descricao:
                return {"sucesso": False, "erro": "Parâmetro 'descricao' é obrigatório"}

            # Valida tamanho da descrição
            if len(descricao) > 250:
                logger.warning(f"Descrição muito longa ({len(descricao)} caracteres). Truncando para 250 caracteres.")
                descricao = descricao[:250]

            logger.info("="*80)
            logger.info("Enviando documento para ADVWin GED")
            logger.info("="*80)
            logger.info(f"Arquivo: {file_path_obj.name}")
            logger.info(f"Tamanho: {file_path_obj.stat().st_size / 1024:.2f} KB")
            logger.info(f"Extensão: {file_path_obj.suffix}")
            logger.info(f"Tabela: {tabela_or}")
            logger.info(f"Código: {codigo_or}")
            logger.info(f"Descrição: {descricao} (len: {len(descricao)})")
            if id_or:
                logger.info(f"ID: {id_or}")
            else:
                logger.warning("ID_OR não fornecido (será omitido do request)")
            if observacao:
                logger.info(f"Observação: {observacao}")
            logger.info("="*80)

            url = f"{self.host}/api/partner/ged/upload"

            # Prepara o arquivo para upload
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path_obj.name, f, 'application/octet-stream')
                }

                # Prepara os dados do formulário
                data = {
                    'Tabela_OR': tabela_or,
                    'Codigo_OR': codigo_or,
                    'descricao': descricao,
                    'Id_OR': id_or if id_or else 'null',  # API aceita string "null"
                    'observacao': observacao if observacao else ''
                }

                logger.info(f"POST {url}")
                logger.info(f"Campos enviados: {list(data.keys())}")
                logger.info(f"Valores dos campos:")
                for key, value in data.items():
                    if len(str(value)) > 100:
                        logger.info(f"  - {key}: {str(value)[:100]}... (truncado)")
                    else:
                        logger.info(f"  - {key}: {value}")
                logger.debug(f"Data completa: {data}")

                # Envia a requisição
                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    timeout=120  # Timeout maior para upload de arquivos
                )

            logger.info(f"Status HTTP: {response.status_code}")

            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    logger.info(f"Response JSON: {response.text[:500]}")  # Log primeiros 500 chars
                except Exception as e:
                    logger.warning(f"Erro ao parsear JSON: {e}")
                    logger.info(f"Response text: {response.text[:500]}")
                    response_data = {"message": response.text}

                # Verifica o status DENTRO do JSON (a API retorna HTTP 200 mesmo com erro!)
                json_status = response_data.get('status', response.status_code)
                logger.info(f"JSON status: {json_status}")

                if json_status in [200, 201]:
                    logger.info("✓ Documento enviado com sucesso!")
                    return {
                        "sucesso": True,
                        "status_code": response.status_code,
                        "dados": response_data,
                        "arquivo": file_path_obj.name
                    }
                else:
                    # API retornou HTTP 200 mas JSON indica erro
                    error_message = response_data.get('message', 'Erro desconhecido')
                    logger.error(f"✗ Erro no upload - JSON status: {json_status}")
                    logger.error(f"✗ Mensagem: {error_message}")
                    logger.error(f"✗ Response completa: {response_data}")

                    return {
                        "sucesso": False,
                        "erro": error_message,
                        "status_code": response.status_code,
                        "json_status": json_status,
                        "detalhes": response_data
                    }

            elif response.status_code == 401:
                logger.warning("Token expirado ou inválido. Tentando renovar...")

                # Tenta fazer login novamente
                if self.login():
                    logger.info("Login renovado. Tentando upload novamente...")
                    # Recursão para tentar novamente com novo token
                    return self.upload_ged(
                        file_path=file_path,
                        tabela_or=tabela_or,
                        codigo_or=codigo_or,
                        descricao=descricao,
                        id_or=id_or,
                        observacao=observacao
                    )
                else:
                    logger.error("Falha ao renovar autenticação")
                    return {
                        "sucesso": False,
                        "erro": "Token expirado e falha ao renovar autenticação",
                        "status_code": 401
                    }

            else:
                logger.error(f"Erro ao enviar documento - Status: {response.status_code}")
                logger.error(f"Response: {response.text}")

                return {
                    "sucesso": False,
                    "erro": f"Erro HTTP {response.status_code}",
                    "status_code": response.status_code,
                    "detalhes": response.text
                }

        except requests.exceptions.Timeout:
            logger.error("Timeout ao tentar enviar documento para ADVWin")
            return {
                "sucesso": False,
                "erro": "Timeout na requisição (mais de 120 segundos)"
            }

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão ao tentar enviar documento: {e}")
            return {
                "sucesso": False,
                "erro": f"Erro de conexão: {str(e)}"
            }

        except Exception as e:
            logger.error(f"Erro inesperado ao enviar documento: {e}")
            import traceback
            logger.error(traceback.format_exc())

            return {
                "sucesso": False,
                "erro": f"Erro inesperado: {str(e)}"
            }


    def upload_multiplos_ged(
        self,
        arquivos: list,
        tabela_or: str,
        codigo_or: str,
        id_or: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia múltiplos arquivos de GED para o ADVWin

        Args:
            arquivos: Lista de dicionários contendo informações dos arquivos:
                [
                    {
                        "caminho": "/path/to/file.pdf",
                        "descricao": "Descrição do arquivo",
                        "observacao": "Observações opcionais"
                    }
                ]
            tabela_or: Tabela de origem (Pastas, Agenda, Debite, Clientes)
            codigo_or: Código de referência
            id_or: ID para movimentação (opcional)

        Returns:
            dict: Resumo dos uploads realizados
        """
        logger.info("="*80)
        logger.info(f"Iniciando envio de {len(arquivos)} arquivo(s) para ADVWin GED")
        logger.info("="*80)

        resultados = {
            "total": len(arquivos),
            "sucesso": 0,
            "falha": 0,
            "detalhes": []
        }

        for idx, arquivo_info in enumerate(arquivos, start=1):
            logger.info(f"\n[{idx}/{len(arquivos)}] Processando arquivo...")

            caminho = arquivo_info.get("caminho")
            descricao = arquivo_info.get("descricao", Path(caminho).stem)
            observacao = arquivo_info.get("observacao", "")

            resultado = self.upload_ged(
                file_path=caminho,
                tabela_or=tabela_or,
                codigo_or=codigo_or,
                descricao=descricao,
                id_or=id_or,
                observacao=observacao
            )

            if resultado.get("sucesso"):
                resultados["sucesso"] += 1
            else:
                resultados["falha"] += 1

            resultados["detalhes"].append({
                "arquivo": Path(caminho).name,
                "resultado": resultado
            })

        logger.info("="*80)
        logger.info("RESUMO DO ENVIO")
        logger.info("="*80)
        logger.info(f"Total de arquivos: {resultados['total']}")
        logger.info(f"✓ Sucesso: {resultados['sucesso']}")
        logger.info(f"✗ Falha: {resultados['falha']}")
        logger.info("="*80)

        return resultados


    def __del__(self):
        """Fecha a sessão quando o objeto é destruído"""
        if hasattr(self, 'session'):
            self.session.close()

"""
Dispatcher para selecionar o sistema RPA apropriado por cliente.
Mapeia códigos de cliente para classes RPA específicas.
"""
import importlib
import logging
from typing import Tuple, Type, Optional, Any

from settings import settings

logger = logging.getLogger(__name__)


# Mapeamento de cliente para módulo e classe RPA
RPA_MAPPING = {
    # eLaw COGNA
    'cogna': ('sistemas.elaw.cogna', 'ElawCOGNA'),
    'mercantil': ('sistemas.elaw.cogna', 'ElawCOGNA'),

    # BCLegal Loft
    'loft': ('sistemas.bclegal.loft', 'BCLegal'),

    # Lexxy SuperSim
    'supersim': ('sistemas.lexxy.supersim', 'LexxySuperSim'),
}

# Mapeamento de cliente para credenciais
CREDENTIALS_MAPPING = {
    'cogna': ('ELAW_USERNAME', 'ELAW_PASSWORD'),
    'mercantil': ('ELAW_USERNAME', 'ELAW_PASSWORD'),
    'loft': ('BCLEGAL_USER', 'BCLEGAL_PASSWORD'),
    'supersim': ('LEXXY_USER', 'LEXXY_PASSWORD'),
}


def get_supported_clients() -> list:
    """Retorna lista de clientes suportados"""
    return list(RPA_MAPPING.keys())


def is_client_supported(cliente_codigo: str) -> bool:
    """Verifica se o cliente é suportado"""
    return cliente_codigo.lower() in RPA_MAPPING


def get_rpa_class(cliente_codigo: str) -> Type[Any]:
    """
    Retorna a classe RPA apropriada para o cliente.

    Args:
        cliente_codigo: Código do cliente (ex: 'cogna', 'loft', 'supersim')

    Returns:
        Classe RPA correspondente

    Raises:
        ValueError: Se o cliente não for suportado
        ImportError: Se o módulo não puder ser importado
    """
    cliente_codigo = cliente_codigo.lower()

    if cliente_codigo not in RPA_MAPPING:
        supported = ", ".join(get_supported_clients())
        raise ValueError(
            f"Cliente '{cliente_codigo}' não suportado. "
            f"Clientes suportados: {supported}"
        )

    module_name, class_name = RPA_MAPPING[cliente_codigo]

    try:
        module = importlib.import_module(module_name)
        rpa_class = getattr(module, class_name)
        logger.debug(f"Classe RPA carregada: {class_name} para cliente {cliente_codigo}")
        return rpa_class
    except ImportError as e:
        logger.error(f"Erro ao importar módulo {module_name}: {e}")
        raise ImportError(f"Não foi possível importar o módulo RPA para {cliente_codigo}: {e}")
    except AttributeError as e:
        logger.error(f"Classe {class_name} não encontrada em {module_name}: {e}")
        raise ImportError(f"Classe RPA '{class_name}' não encontrada: {e}")


def get_credentials_for_client(cliente_codigo: str) -> Tuple[str, str]:
    """
    Retorna as credenciais de login para o cliente.

    Args:
        cliente_codigo: Código do cliente

    Returns:
        Tupla (username, password)

    Raises:
        ValueError: Se o cliente não for suportado
    """
    cliente_codigo = cliente_codigo.lower()

    if cliente_codigo not in CREDENTIALS_MAPPING:
        raise ValueError(f"Credenciais não configuradas para cliente '{cliente_codigo}'")

    username_key, password_key = CREDENTIALS_MAPPING[cliente_codigo]

    username = getattr(settings, username_key, "")
    password = getattr(settings, password_key, "")

    if not username or not password:
        logger.warning(
            f"Credenciais incompletas para {cliente_codigo}. "
            f"Verifique {username_key} e {password_key} no settings."
        )

    return username, password


def get_rpa_system_name(cliente_codigo: str) -> str:
    """
    Retorna o nome do sistema RPA para o cliente.

    Args:
        cliente_codigo: Código do cliente

    Returns:
        Nome do sistema (ex: 'elaw_cogna', 'bclegal', 'lexxy')
    """
    cliente_codigo = cliente_codigo.lower()

    system_names = {
        'cogna': 'elaw_cogna',
        'mercantil': 'elaw_cogna',
        'loft': 'bclegal',
        'supersim': 'lexxy',
    }

    return system_names.get(cliente_codigo, 'unknown')


def create_rpa_instance(
    cliente_codigo: str,
    driver: Any,
    download_path: Optional[str] = None
) -> Any:
    """
    Cria uma instância do RPA apropriado para o cliente.

    Args:
        cliente_codigo: Código do cliente
        driver: WebDriver do Selenium
        download_path: Caminho para downloads (opcional)

    Returns:
        Instância da classe RPA configurada
    """
    import os

    RpaClass = get_rpa_class(cliente_codigo)
    username, password = get_credentials_for_client(cliente_codigo)

    if download_path is None:
        download_path = os.path.join(os.path.expanduser("~"), "Downloads")

    # Instancia a classe RPA com os parâmetros necessários
    rpa_instance = RpaClass(
        driver=driver,
        usuario=username,
        senha=password,
        download_path=download_path
    )

    logger.info(f"Instância RPA criada para cliente: {cliente_codigo}")
    return rpa_instance


def get_download_method_name(cliente_codigo: str) -> str:
    """
    Retorna o nome do método de download para o cliente.
    Diferentes sistemas podem ter nomes de métodos diferentes.

    Args:
        cliente_codigo: Código do cliente

    Returns:
        Nome do método de download
    """
    # Por padrão, todos usam o mesmo nome de método
    # Mas pode ser customizado por cliente se necessário
    method_mapping = {
        'cogna': 'baixa_documento_anexo',
        'mercantil': 'baixa_documento_anexo',
        'loft': 'baixa_documento_anexo',
        'supersim': 'baixa_documento_anexo',
    }

    return method_mapping.get(cliente_codigo.lower(), 'baixa_documento_anexo')

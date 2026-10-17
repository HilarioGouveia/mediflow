"""
Adaptador de Infraestrutura: OCI Object Storage Always Free
Implementa StoragePort com suporte ao SDK oficial OCI e fallback tolerante em memória
para ambientes locais de teste e desenvolvimento sem credenciais configuradas.
"""

import json
import logging
from io import BytesIO
from typing import Any, Dict, List, Optional, Union
import oci

from domain.ports.storage_port import StoragePort

logger = logging.getLogger("MediFlowStorage")


class OCIStorageAdapter(StoragePort):
    """
    Adaptador de persistência para Oracle Cloud Infrastructure (OCI Always Free).
    Garante segregação entre /recebidos/, /processados/ e /auditoria_humana/.
    Se config_dict for vazio ou inválido, ativa contingência simulada em memória.
    """

    def __init__(self, config_dict: dict, namespace_name: str):
        self.namespace = namespace_name
        self.simulado = not bool(config_dict)
        self.armazenamento_local: Dict[str, bytes] = {}  # Buffer em memória para modo simulado

        if not self.simulado:
            try:
                self.client = oci.object_storage.ObjectStorageClient(config_dict)
                logger.info("Cliente OCI Object Storage inicializado com sucesso.")
            except Exception as exc:
                logger.warning(
                    "Falha ao instanciar SDK OCI (%s). Ativando modo de contingência em memória.",
                    exc
                )
                self.simulado = True
                self.client = None
        else:
            logger.info("OCI Storage Adapter operando em modo simulado/contingência.")
            self.client = None

    def salvar_arquivo(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Persiste um arquivo bruto (PDF, imagem ou texto) sob o prefixo configurado (ex.: /recebidos/).
        Retorna o caminho lógico do objeto criado.
        """
        caminho_completo = f"{self.namespace}/{bucket_name}/{object_name}"

        if self.simulado:
            self.armazenamento_local[object_name] = bytes(data)
            logger.info("[SIMULADO] Arquivo persistido: %s", caminho_completo)
            return caminho_completo

        try:
            stream = BytesIO(data)
            self.client.put_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name,
                put_object_body=stream,
                content_type=content_type,
            )
            logger.info("Arquivo enviado com sucesso para OCI: %s", caminho_completo)
            return caminho_completo
        except Exception as exc:
            logger.error("Erro ao subir arquivo %s para OCI Object Storage: %s", object_name, exc)
            return ""

    def salvar_json(
        self,
        bucket_name: str,
        object_name: str,
        json_data: Union[Dict[str, Any], List[Any], str]
    ) -> bool:
        """
        Serializa e persiste o relatório de triagem estruturado em JSON no OCI.
        Aceita dicionários, listas ou strings pré-formatadas.
        """
        try:
            if isinstance(json_data, (dict, list)):
                payload = json.dumps(json_data, ensure_ascii=False, indent=2).encode("utf-8")
            else:
                payload = str(json_data).encode("utf-8")

            if self.simulado:
                self.armazenamento_local[object_name] = payload
                logger.info("[SIMULADO] JSON persistido em: %s/%s", bucket_name, object_name)
                return True

            stream = BytesIO(payload)
            self.client.put_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name,
                put_object_body=stream,
                content_type="application/json; charset=utf-8",
            )
            logger.info("JSON persistido com sucesso no OCI: %s/%s", bucket_name, object_name)
            return True
        except Exception as exc:
            logger.error("Erro ao salvar JSON %s no OCI Object Storage: %s", object_name, exc)
            return False

    def obter_json(self, bucket_name: str, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Recupera e decodifica um relatório JSON diretamente do OCI ou do buffer local.
        """
        try:
            if self.simulado:
                raw_bytes = self.armazenamento_local.get(object_name)
                return json.loads(raw_bytes.decode("utf-8")) if raw_bytes else None

            resposta = self.client.get_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name,
            )
            conteudo = resposta.data.content.decode("utf-8")
            return json.loads(conteudo)
        except Exception as exc:
            logger.error("Erro ao recuperar objeto JSON %s do OCI: %s", object_name, exc)
            return None

    def listar_objetos_por_prefixo(self, bucket_name: str, prefixo: str) -> List[str]:
        """
        Lista todas as chaves de objetos contidas em um determinado prefixo/pasta virtual
        (ex.: 'processados/urgentes/' ou 'auditoria_humana/').
        """
        if self.simulado:
            return [chave for chave in self.armazenamento_local.keys() if chave.startswith(prefixo)]

        try:
            resposta = self.client.list_objects(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                prefix=prefixo,
            )
            return [obj.name for obj in resposta.data.objects]
        except Exception as exc:
            logger.error("Erro ao listar objetos com prefixo '%s' no OCI: %s", prefixo, exc)
            return []

    def mover_objeto(
        self,
        bucket_name: str,
        origem: str,
        destino: str,
        novos_dados: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Move e atualiza um objeto entre pastas virtuais (ex.: de auditoria_humana/ para processados/rotina/).
        Salva os novos dados no destino e remove a chave antiga da origem.
        """
        try:
            dados = novos_dados if novos_dados else self.obter_json(bucket_name, origem)
            if not dados:
                logger.warning("Objeto de origem '%s' não encontrado para movimentação.", origem)
                return False

            # 1. Salvar no novo caminho
            sucesso_salvar = self.salvar_json(bucket_name, destino, dados)
            if not sucesso_salvar:
                return False

            # 2. Deletar do caminho anterior
            if self.simulado:
                self.armazenamento_local.pop(origem, None)
                logger.info("[SIMULADO] Objeto movido com sucesso de '%s' para '%s'", origem, destino)
                return True

            self.client.delete_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=origem,
            )
            logger.info("Objeto movido com sucesso no OCI de '%s' para '%s'", origem, destino)
            return True

        except Exception as exc:
            logger.error("Falha ao mover objeto de '%s' para '%s' no OCI: %s", origem, destino, exc)
            return False
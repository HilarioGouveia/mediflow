r"""Validação real, com dados sintéticos e armazenamento em memória.

Uso: .venv\Scripts\python.exe scripts/validar_gemini.py [--multimodal]
Não testa OCI real nem entrega externa de alertas.
"""
import argparse
import base64
from io import BytesIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.dtos.input_request import TriagemRequestDTO
from application.use_cases.processar_triagem import ProcessarTriagemUseCase
from config.settings import settings
from infrastructure.adapters.gemini_llm_adapter import GeminiLLMAdapter
from infrastructure.adapters.memory_storage_adapter import MemoryStorageAdapter


class NotificadorTeste:
    def enviar_alerta_urgencia(self, **kwargs):
        return False  # Nenhuma mensagem é enviada a terceiros.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--multimodal", action="store_true", help="Também faz chamadas reais com PDF e PNG sintéticos.")
    args = parser.parse_args()
    if not settings.GEMINI_API_KEY.strip():
        print("Chave ausente. Configure GEMINI_API_KEY.")
        return 1
    rotina = "RECEITA MEDICA FICTICIA. Paciente: Ana Teste, 34 anos. Medica: Maria Exemplo, CRM 123456-SP. Paracetamol 500 mg, um comprimido a cada 8 horas por 2 dias. Consulta ambulatorial sem sinais de urgencia."
    cenarios = [
        ("rotina", "TEXTO", rotina, "Farmacia_Hospitalar"),
        ("urgencia", "TEXTO", "LAUDO FICTICIO. Paciente Carlos Teste, 52 anos. Solicitante Maria Exemplo, CRM 123456-SP. Angiotomografia de torax: tromboembolismo pulmonar agudo grave, com dispneia e instabilidade hemodinamica. Atendimento de emergencia imediato.", "Fila_Emergencia_Medica"),
        ("ambiguidade", "TEXTO", "GUIA RASURADA. Paciente: [ilegivel]. Medico e CRM: [ausentes]. Procedimento: [ilegivel].", "Fila_Revisao_Humana"),
    ]
    if args.multimodal:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        imagem = Image.new("RGB", (1100, 650), "white")
        ImageDraw.Draw(imagem).multiline_text((40, 50), "\n".join(textwrap.wrap(rotina, 65)), font=ImageFont.load_default(size=24), fill="black", spacing=14)
        for tipo, formato in (("PDF", "PDF"), ("IMAGEM", "PNG")):
            stream = BytesIO()
            imagem.save(stream, format=formato)
            cenarios.append((formato.lower(), tipo, base64.b64encode(stream.getvalue()).decode(), "Farmacia_Hospitalar"))
    adapter = GeminiLLMAdapter(settings.GEMINI_API_KEY, settings.GEMINI_MODEL_NAME, timeout_ms=settings.GEMINI_TIMEOUT_MS, max_attempts=1)
    caso = ProcessarTriagemUseCase(adapter, MemoryStorageAdapter(), NotificadorTeste(), "validacao-local")
    print("Modelo:", settings.GEMINI_MODEL_NAME, flush=True)
    falhas = 0
    for nome, tipo, conteudo, esperado in cenarios:
        print("Validando:", nome, flush=True)
        request = TriagemRequestDTO(documento_id=f"TESTE-{nome}", tipo_arquivo=tipo, canal_origem="Validacao_Sintetica", documento_texto=conteudo if tipo == "TEXTO" else None, arquivo_base64=conteudo if tipo != "TEXTO" else None)
        resultado = caso.executar(request)
        erro = resultado.erro_extracao
        destino = resultado.decisao_roteamento.destino_principal
        aprovado = not erro and destino == esperado
        if nome != "ambiguidade" and not erro:
            aprovado = aprovado and bool(resultado.dados_extraidos.paciente.nome) and bool(resultado.dados_extraidos.medico_solicitante.crm)
        print("APROVADO" if aprovado else "FALHOU", nome, erro.codigo if erro else destino, flush=True)
        if erro:
            print("Validação interrompida:", erro.mensagem, flush=True)
            return 1
        falhas += not aprovado
    print("Validação sintética concluída. OCI e alertas externos não foram testados.")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())

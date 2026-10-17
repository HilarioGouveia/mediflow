"""
Suíte de Demonstração e Validação Automatizada dos 3 Cenários Canônicos.
Executa asserções estritas (assert) contra os critérios de aceite do Hackathon ONE G10.
Pode ser executado diretamente (python tests/demonstracao_cenarios.py) ou via pytest.
"""

import sys
import requests
from typing import Dict, Any

API_URL = "http://localhost:8000/triagem"


def assert_cenario(condicao: bool, mensagem_erro: str):
    """Auxiliar para validação de critérios com feedback estruturado."""
    if not condicao:
        print(f"❌ FALHA DE ASSERÇÃO: {mensagem_erro}")
        raise AssertionError(mensagem_erro)


def test_cenario_1_rotina_aprovada():
    """
    CENÁRIO 1: Fluxo de Rotina Aprovado.
    Critérios:
    - Identificação válida de paciente e CRM com UF.
    - Score >= 0.85.
    - Automação sem intervenção humana (requer_auditoria_humana == False).
    - Persistência estruturada em 'processados/rotina/'.
    """
    print("\n[TESTE 1/3] Executando Cenário de Rotina Aprovada...")
    
    payload = {
        "documento_id": "DOC-ROTINA-2026-101",
        "tipo_arquivo": "TEXTO",
        "documento_texto": (
            "RECEITUÁRIO MÉDICO AMBULATORIAL. "
            "Paciente: Ana Beatriz Silva, 34 anos. "
            "Médico Solicitante: Dr. Roberto Guimarães CRM-SP 89452. "
            "Prescrição: Amoxicilina 500mg - Tomar 1 cápsula via oral a cada 8 horas por 7 dias. "
            "Dipirona 500mg - 1 comprimido se dor ou febre."
        ),
        "canal_origem": "Ambulatorio"
    }

    resp = requests.post(API_URL, json=payload, timeout=60)
    assert_cenario(resp.status_code == 200, f"API retornou status {resp.status_code}: {resp.text}")
    
    dados: Dict[str, Any] = resp.json()

    # Validações estruturais e de negócio
    assert_cenario(dados["status"] == "processado", "Status deve ser 'processado'")
    assert_cenario(dados["classificacao"]["score_confianca_classificacao"] >= 0.85, "Score deve ser >= 0.85")
    assert_cenario(dados["decisao_roteamento"]["requer_auditoria_humana"] is False, "Não deve requerer auditoria humana")
    assert_cenario(dados["decisao_roteamento"]["destino_principal"] in ["Farmacia_Hospitalar", "Prontuario_Eletronico_Paciente"], 
                   f"Destino incompatível com receituário: {dados['decisao_roteamento']['destino_principal']}")
    
    caminho_oci = dados["armazenamento_oci"]["caminho_objeto"]
    assert_cenario("processados/rotina/" in caminho_oci, f"Caminho OCI incorreto para rotina: {caminho_oci}")
    assert_cenario(dados["armazenamento_oci"]["caminho_documento_bruto"] is not None, "Documento original deve ser salvo em recebidos/")

    print(f"  ✓ Classificação: {dados['classificacao']['tipo_documento']}")
    print(f"  ✓ Score: {dados['classificacao']['score_confianca_classificacao'] * 100:.1f}%")
    print(f"  ✓ Destino: {dados['decisao_roteamento']['destino_principal']}")
    print(f"  ✓ OCI Path: {caminho_oci}")
    print("✅ Cenário 1 Aprovado com Sucesso!")


def test_cenario_2_urgencia_critica():
    """
    CENÁRIO 2: Urgência Médica Crítica com Notificação Imediata.
    Critérios:
    - Diagnóstico crítico de Tromboembolismo Pulmonar Agudo (TEP).
    - Prioridade 'Urgente' e encaminhamento para 'Fila_Emergencia_Medica'.
    - requer_auditoria_humana == False (despacho sem bloqueio burocrático).
    - Geração de notificação de alerta para o plantão médico.
    - Persistência em 'processados/urgentes/'.
    """
    print("\n[TESTE 2/3] Executando Cenário de Urgência Médica (TEP Agudo)...")

    payload = {
        "documento_id": "DOC-CLIN-2026-8942",
        "tipo_arquivo": "TEXTO",
        "documento_texto": (
            "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO. "
            "Paciente: Carlos Eduardo Mendes, 52 anos. "
            "Solicitante: Dra. Renata Silveira CRM-SP 145892. "
            "Exame: Angiotomografia de Tórax com contraste venoso. "
            "Indicação: Suspeita de embolia pulmonar aguda com taquipneia. "
            "Achados: Falha de enchimento oclusiva em tronco pulmonar principal direito, "
            "caracterizando Tromboembolismo Pulmonar Agudo (TEP). "
            "CONCLUSÃO: Quadro compatível com Tromboembolismo Pulmonar Agudo grave."
        ),
        "canal_origem": "Pronto_Socorro"
    }

    resp = requests.post(API_URL, json=payload, timeout=60)
    assert_cenario(resp.status_code == 200, f"API retornou status {resp.status_code}: {resp.text}")

    dados: Dict[str, Any] = resp.json()

    # Validações de urgência e alerta
    assert_cenario(dados["classificacao"]["nivel_prioridade"] == "Urgente", "Prioridade deve ser 'Urgente'")
    assert_cenario(dados["decisao_roteamento"]["destino_principal"] == "Fila_Emergencia_Medica", 
                   f"Destino deve ser emergência: {dados['decisao_roteamento']['destino_principal']}")
    assert_cenario(dados["decisao_roteamento"]["requer_auditoria_humana"] is False, "Emergência não pode ser retida")
    
    notificacao = dados["decisao_roteamento"].get("notificacao_gerada")
    assert_cenario(notificacao is not None, "Deve gerar notificação de alerta imediato")
    assert_cenario(notificacao["canal"] == "Alerta_Plantao_Medico", "Canal de alerta deve ser o plantão médico")
    
    caminho_oci = dados["armazenamento_oci"]["caminho_objeto"]
    assert_cenario("processados/urgentes/" in caminho_oci, f"Caminho OCI incorreto para urgência: {caminho_oci}")

    print(f"  ✓ Diagnóstico: {dados['dados_extraidos']['diagnostico_principal']}")
    print(f"  ✓ Prioridade: {dados['classificacao']['nivel_prioridade']}")
    print(f"  ✓ Notificação: {notificacao['mensagem']}")
    print(f"  ✓ OCI Path: {caminho_oci}")
    print("✅ Cenário 2 Aprovado com Sucesso!")


def test_cenario_3_ambiguidade_auditoria():
    """
    CENÁRIO 3: Ambiguidade / Falha Cadastral (Human-in-the-Loop).
    Critérios:
    - Documento com rasura, ausência de CRM e nome ilegível.
    - Ativação obrigatória de contingência (requer_auditoria_humana == True).
    - Desvio para 'Fila_Revisao_Humana'.
    - Persistência no prefixo 'auditoria_humana/'.
    """
    print("\n[TESTE 3/3] Executando Cenário de Ambiguidade / Auditoria Humana...")

    payload = {
        "documento_id": "DOC-AMBIGUO-2026-404",
        "tipo_arquivo": "TEXTO",
        "documento_texto": (
            "GUIA DE ATENDIMENTO MÉDICO COM RASURA. "
            "Paciente: [Ilegível / Rasurado]. Idade: não informada. "
            "Médico Solicitante: Dr. [borrado], CRM: [em branco]. "
            "Procedimento solicitado: Exame complementar de imagem. "
            "Justificativa com texto ilegível devido a falha na digitalização."
        ),
        "canal_origem": "Recepcao"
    }

    resp = requests.post(API_URL, json=payload, timeout=60)
    assert_cenario(resp.status_code == 200, f"API retornou status {resp.status_code}: {resp.text}")

    dados: Dict[str, Any] = resp.json()

    # Validações do fallback humano
    assert_cenario(dados["decisao_roteamento"]["requer_auditoria_humana"] is True, 
                   "Documento ilegível/sem CRM deve exigir auditoria humana")
    assert_cenario(dados["decisao_roteamento"]["destino_principal"] == "Fila_Revisao_Humana", 
                   f"Destino deve ser fila humana: {dados['decisao_roteamento']['destino_principal']}")
    
    justificativa = dados["decisao_roteamento"]["justificativa_roteamento"]
    assert_cenario(len(justificativa) > 10, "Justificativa da retenção deve ser preenchida")

    caminho_oci = dados["armazenamento_oci"]["caminho_objeto"]
    assert_cenario("auditoria_humana/" in caminho_oci, f"Caminho OCI incorreto para auditoria: {caminho_oci}")

    print(f"  ✓ Requer Auditoria Humana: {dados['decisao_roteamento']['requer_auditoria_humana']}")
    print(f"  ✓ Justificativa: {justificativa}")
    print(f"  ✓ OCI Path: {caminho_oci}")
    print("✅ Cenário 3 Aprovado com Sucesso!")


if __name__ == "__main__":
    print("==================================================================")
    print("   MEDIFLOW — VALIDAÇÃO DOS 3 CENÁRIOS OBRIGATÓRIOS DO HACKATHON  ")
    print("==================================================================")
    try:
        test_cenario_1_rotina_aprovada()
        test_cenario_2_urgencia_critica()
        test_cenario_3_ambiguidade_auditoria()
        print("\n🎉 TODOS OS 3 CENÁRIOS FORAM VALIDADOS COM SUCESSO (100% DE COBERTURA)!\n")
        sys.exit(0)
    except AssertionError as err:
        print(f"\n❌ INTERRUPÇÃO: O teste falhou no critério de aceite: {err}\n")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO DE CONEXÃO: Certifique-se de que a API está ativa em http://localhost:8000 antes de executar.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ ERRO INESPERADO: {exc}")
        sys.exit(1)
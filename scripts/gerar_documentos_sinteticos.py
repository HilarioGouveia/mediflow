"""Gera fixtures documentais sem dados reais. Requer reportlab, Pillow e Poppler."""
from datetime import date
from io import BytesIO
from pathlib import Path
import json
import shutil
import subprocess
import zipfile
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter, ImageOps
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/mediflow-testes-sinteticos"

CASOS = [
    dict(id="TC01", nome="receita_rotina", titulo="Receituário médico", paciente="Paciente Sintético Alfa", idade=34,
         medico="Dra. Profissional Simulada A", crm="123456-SP", prioridade="Rotina", especialidade="Clínica Geral",
         diagnostico="Registro de atendimento ambulatorial sem sinais de gravidade.", exame=None, cid=None,
         medicamentos=["Medicamento Simulado A (substância fictícia), 10 mg; 1 comprimido por via oral, 1 vez ao dia, por 3 dias. Posologia criada apenas para teste."],
         texto="Paciente estável. Documento completo e legível. Sem achado crítico ou indicação de atendimento urgente.",
         destino="Farmacia_Hospitalar", auditoria=False, prefixo="processados/rotina/", score="maior_ou_igual_0.85", critico=False),
    dict(id="TC02", nome="laudo_urgente", titulo="Laudo de exame de imagem", paciente="Paciente Sintético Beta", idade=52,
         medico="Dra. Profissional Simulada B", crm="234567-SP", prioridade="Urgente", especialidade="Radiologia",
         diagnostico="Tromboembolismo pulmonar agudo.", exame="Angiotomografia de tórax", cid="I26.9", medicamentos=[],
         texto="Achados: falhas de enchimento em artérias pulmonares, compatíveis com tromboembolismo pulmonar agudo. Paciente com dispneia súbita e instabilidade hemodinâmica. Conclusão: achado crítico; atendimento médico emergencial imediato indicado neste cenário fictício.",
         destino="Fila_Emergencia_Medica", auditoria=False, prefixo="processados/urgentes/", score="maior_ou_igual_0.85", critico=True),
    dict(id="TC03", nome="guia_ambigua", titulo="Guia de solicitação de procedimento", paciente=None, idade=None,
         medico=None, crm=None, prioridade="Não determinável", especialidade="Não identificada",
         diagnostico=None, exame="Exame de imagem não especificado", cid=None, medicamentos=[],
         texto="Documento com campos incompletos. Nome do paciente: [ilegível]. Profissional solicitante: [rasurado]. CRM: [ausente]. Justificativa: [ilegível]. Não é possível reconstruir os dados ausentes.",
         destino="Fila_Revisao_Humana", auditoria=True, prefixo="auditoria_humana/", score="menor_0.85", critico=False),
    dict(id="TC04", nome="guia_rotina", titulo="Guia de autorização de procedimento", paciente="Paciente Sintético Gama", idade=41,
         medico="Dr. Profissional Simulado C", crm="345678-RJ", prioridade="Rotina", especialidade="Clínica Geral",
         diagnostico="Avaliação ambulatorial programada.", exame="Hemograma completo", cid=None, medicamentos=[],
         texto="Solicitação eletiva de exame para acompanhamento ambulatorial. Sem sintomas agudos ou achados críticos. Dados cadastrais completos e legíveis.",
         destino="Auditoria_de_Autorizacoes", auditoria=False, prefixo="processados/rotina/", score="maior_ou_igual_0.85", critico=False),
    dict(id="TC05", nome="receita_sem_medicamento", titulo="Receituário médico", paciente="Paciente Sintético Delta", idade=29,
         medico="Dra. Profissional Simulada D", crm="456789-MG", prioridade="Rotina", especialidade="Clínica Geral",
         diagnostico="Não registrado no documento.", exame=None, cid=None, medicamentos=[],
         texto="Campo de prescrição deixado em branco. Não há nome de medicamento, dose, frequência ou duração. Documento intitulado receituário, mas sem prescrição preenchida. Sem indicação de urgência.",
         destino="Fila_Revisao_Humana", auditoria=True, prefixo="auditoria_humana/", score="nao_fixado", critico=False),
    dict(id="TC06", nome="laudo_sem_crm", titulo="Laudo de exame laboratorial", paciente="Paciente Sintético Épsilon", idade=45,
         medico="Dr. Profissional Simulado E", crm=None, prioridade="Rotina", especialidade="Medicina Laboratorial",
         diagnostico="Sem alteração crítica descrita.", exame="Hemograma completo", cid=None, medicamentos=[],
         texto="Laudo legível e identificado. Nenhum resultado crítico descrito. O campo de CRM não foi preenchido. Documento sem identificação completa do profissional responsável.",
         destino="Fila_Revisao_Humana", auditoria=True, prefixo="auditoria_humana/", score="nao_fixado", critico=False),
    dict(id="TC07", nome="guia_prioritaria", titulo="Guia de autorização de procedimento", paciente="Paciente Sintético Zeta", idade=67,
         medico="Dra. Profissional Simulada F", crm="567890-PR", prioridade="Prioritário", especialidade="Clínica Geral",
         diagnostico="Acompanhamento ambulatorial prioritário.", exame="Ultrassonografia abdominal", cid=None, medicamentos=[],
         texto="Prioridade registrada expressamente pelo solicitante: PRIORITÁRIO. Atendimento ambulatorial com prioridade, sem achado crítico ou emergência. Dados completos e legíveis.",
         destino="Auditoria_de_Autorizacoes", auditoria=False, prefixo="processados/prioritário/", score="maior_ou_igual_0.85", critico=False),
]


def campos(caso):
    return [
        ("Paciente", caso['paciente'] or "[ilegível / não identificado]"),
        ("Idade", str(caso['idade']) + " anos" if caso['idade'] is not None else "[não informada]"),
        ("Profissional", caso['medico'] or "[rasurado / não identificado]"),
        ("CRM / UF", caso['crm'] or "[ausente]"),
        ("Especialidade", caso['especialidade']), ("Prioridade registrada", caso['prioridade']),
        ("Exame / procedimento", caso['exame'] or "Não informado"),
        ("Diagnóstico / hipótese", caso['diagnostico'] or "[não legível]"),
        ("CID informado", caso['cid'] or "Não informado"),
    ]


def gerar_pdf(caso, path):
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle('TituloTeste', fontName='Helvetica-Bold', fontSize=20, leading=25, textColor=colors.HexColor('#125e65'), spaceAfter=15))
    estilos.add(ParagraphStyle('TextoTeste', fontName='Helvetica', fontSize=10.5, leading=16, spaceAfter=8))
    estilos.add(ParagraphStyle('AvisoTeste', fontName='Helvetica-Bold', fontSize=9, leading=13, textColor=colors.HexColor('#9d3e15'), alignment=TA_CENTER))
    p = lambda texto: Paragraph(escape(str(texto)), estilos['TextoTeste'])
    story = [Paragraph('SIMULAÇÃO - DADOS SINTÉTICOS - SEM VALOR CLÍNICO', estilos['AvisoTeste']), Spacer(1, 22),
             p('MediFlow | Unidade de simulação documental'), Paragraph(escape(caso['titulo']), estilos['TituloTeste']),
             p(f"Documento: SYN-{caso['id']} | Emissão fictícia: 17/10/2026")]
    tabela = Table([[p(k), p(v)] for k, v in campos(caso)], colWidths=[136, 355], hAlign='LEFT')
    tabela.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#eef5f5')), ('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#dce5e6')), ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),9), ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story += [tabela, Spacer(1, 18), p('Descrição documental'), p(caso['texto']), p('Prescrição / medicamentos')]
    story += [p(m) for m in caso['medicamentos']] if caso['medicamentos'] else [p('Nenhum medicamento informado neste documento.')]
    story += [Spacer(1, 14), p('Todos os nomes, vínculos profissionais e registros deste documento são fictícios. Os números de CRM servem apenas à validação sintática; não comprovam registro profissional.')]
    def rodape(c, doc):
        c.setStrokeColor(colors.HexColor('#dce5e6'))
        c.line(52, 47, A4[0]-52, 47)
        c.setFont('Helvetica', 8)
        c.setFillColor(colors.HexColor('#52666e'))
        c.drawString(52, 33, f"MediFlow | SYN-{caso['id']} | Uso exclusivo em teste controlado")
        c.drawRightString(A4[0]-52, 33, str(doc.page))
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=52, rightMargin=52, topMargin=42, bottomMargin=65).build(story, onFirstPage=rodape, onLaterPages=rodape)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    poppler = shutil.which('pdftoppm')
    if not poppler:
        raise RuntimeError('pdftoppm não encontrado.')
    manifesto = []
    previews = []
    for caso in CASOS:
        pasta = OUT / 'documentos' / f"{caso['id']}_{caso['nome']}"
        pasta.mkdir(parents=True, exist_ok=True)
        texto = '\n'.join(['SIMULAÇÃO - DADOS SINTÉTICOS - SEM VALOR CLÍNICO', caso['titulo'], f"Documento: SYN-{caso['id']}", 'Emissão fictícia: 17/10/2026', *[f'{k}: {v}' for k,v in campos(caso)], '', caso['texto'], '', 'Medicamentos:', *(caso['medicamentos'] or ['Nenhum medicamento informado.']), '', 'Identificações e registros profissionais fictícios.'])
        (pasta/'documento.txt').write_text(texto+'\n',encoding='utf-8')
        documento = {'aviso': 'Documento integralmente sintético; sem valor clínico.', 'documento_id': f"SYN-{caso['id']}", 'tipo_documento': caso['titulo'], 'paciente': {'nome': caso['paciente'], 'idade': caso['idade']}, 'profissional': {'nome': caso['medico'], 'crm': caso['crm']}, 'prioridade_registrada': caso['prioridade'], 'especialidade': caso['especialidade'], 'exame': caso['exame'], 'diagnostico': caso['diagnostico'], 'cid_informado': caso['cid'], 'medicamentos': caso['medicamentos'], 'descricao': caso['texto']}
        (pasta/'documento.json').write_text(json.dumps(documento,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        gerar_pdf(caso,pasta/'documento.pdf')
        assert len(PdfReader(pasta/'documento.pdf').pages)==1, caso['id']
        subprocess.run([poppler, '-f','1','-singlefile','-r','144','-png', str(pasta/'documento.pdf'), str(pasta/'documento')],check=True, capture_output=True)
        with Image.open(pasta/'documento.png') as img:
            imagem=img.convert('RGB')
        imagem.save(pasta/'documento.jpg',quality=90)
        if caso['id'] in ('TC01','TC02','TC03'):
            scan=ImageOps.grayscale(imagem).filter(ImageFilter.GaussianBlur(.35))
            scan=scan.rotate(.25,resample=Image.Resampling.BICUBIC,expand=False,fillcolor=248).convert('RGB')
            stream=BytesIO()
            scan.save(stream,format='JPEG',quality=82)
            c=canvas.Canvas(str(pasta/'documento_digitalizado.pdf'),pagesize=A4)
            c.drawImage(ImageReader(BytesIO(stream.getvalue())),0,0,width=A4[0],height=A4[1])
            c.save()
            assert not PdfReader(pasta/'documento_digitalizado.pdf').pages[0].extract_text().strip()
        thumb=imagem.copy()
        thumb.thumbnail((280,400))
        previews.append((caso['id'],thumb))
        arquivos = {p.suffix[1:] if p.stem=='documento' else 'pdf_digitalizado': p.relative_to(OUT).as_posix() for p in sorted(pasta.iterdir()) if p.is_file()}
        manifesto.append({'caso':caso['id'],'descricao':caso['nome'],'arquivos':arquivos,'esperado':{'destino_principal':caso['destino'],'requer_auditoria_humana':caso['auditoria'],'prefixo_atual':caso['prefixo'],'achado_critico':caso['critico'],'score_regra':caso['score'],'paciente_nome':caso['paciente'],'crm':caso['crm'],'medicamentos_presentes':bool(caso['medicamentos']),'alerta_plantao_gerado':caso['critico']},'observacao':'Divergência conhecida: o código atual usa processados/prioritário/; o SDD descreve processados/prioritarios/.' if caso['id']=='TC07' else ''})
    for caso, entrada in zip(CASOS, manifesto):
        entrada['esperado'].update({
            'paciente_idade': caso['idade'],
            'exame_mencionado': caso['exame'],
            'cid_informado': caso['cid'],
            'medicamentos_referencia': caso['medicamentos'],
            'prioridade_registrada': caso['prioridade'],
        })
    (OUT/'GABARITO.json').write_text(json.dumps({'versao':'1.0','data':'2026-10-17','natureza':'dados inteiramente sintéticos','casos':manifesto},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    requisicoes=OUT/'requisicoes_api'
    requisicoes.mkdir(exist_ok=True)
    for caso in manifesto:
        texto=(OUT/caso['arquivos']['txt']).read_text(encoding='utf-8')
        payload={'documento_id':f"SYN-{caso['caso']}-TXT-R01",'tipo_arquivo':'TEXTO','documento_texto':texto,'canal_origem':'Teste_Controlado'}
        (requisicoes/f"{caso['caso']}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    guia = '''# MediFlow - teste documental controlado

Todos os documentos são sintéticos, sem pessoas reais ou validade clínica. Os registros
profissionais são valores de teste, sem verificação de existência. Medicamentos e
posologias simulados não são instruções de tratamento.

## Como usar

1. Abra http://localhost:8501 e confirme o modo "OCI emulado localmente".
2. Comece pelo PDF digital do TC01, TC02 e TC03, em Nova triagem > Arquivo.
3. Use um ID exclusivo por caso, formato e rodada: SYN-TC01-PDF-R01.
4. Confira os campos com o documento original e compare o destino com GABARITO.json.
5. Repita com PNG, JPG, PDF digitalizado e JSON. Para TXT, use upload ou cole o conteúdo.
6. Registre: ID, formato, modelo, rodada, status de extração, score, campos divergentes,
   destino, motivo e status do armazenamento. Salve o resultado JSON pelo painel.
7. Execute ao menos três rodadas por cenário para observar variação do modelo.

Não envie GABARITO.json ou este guia como documentos clínicos: eles contêm as respostas.
Os JSONs em documentos/ representam o documento clínico, para upload no painel.
Os JSONs em requisicoes_api/ são requisições prontas para POST /triagem; não são o mesmo formato.
Altere documento_id a cada execução para evitar sobrescrita e notificações repetidas.

## Matriz de aceite

| Caso | Variação | Encaminhamento esperado |
|---|---|---|
| TC01 | Receita completa, sem gravidade | Farmacia_Hospitalar |
| TC02 | Laudo com TEP agudo e dados completos | Fila_Emergencia_Medica |
| TC03 | Paciente ilegível e CRM ausente | Fila_Revisao_Humana |
| TC04 | Guia eletiva, dados completos | Auditoria_de_Autorizacoes |
| TC05 | Receita sem medicamento/posologia | Fila_Revisao_Humana |
| TC06 | Laudo não urgente, CRM ausente | Fila_Revisao_Humana |
| TC07 | Guia com prioridade explícita, sem emergência | Auditoria_de_Autorizacoes |

TC01, TC02, TC04 e TC07 pressupõem confiança >= 0,85; registre como divergência
se o modelo produzir confiança menor e o grafo encaminhar para auditoria. TC03 deve
ter baixa confiança. TC05 e TC06 exigem auditoria independentemente do score.
Não se exige um score numérico exato nem uma descrição textual idêntica ao gabarito.
Compare identidade, presença/ausência de dados e significado dos campos clínicos.

No TC07, a pasta atual é processados/prioritário/. O SDD descreve processados/prioritarios/.
Esta diferença foi registrada no gabarito, sem alterar a implementação do app.

## Auditoria e persistência

No TC03, retifique com Paciente Sintético Revisado, CRM 678901-SP e parecer
"Revisão sintética controlada". Aprovar para prontuário deve retirar o registro da
fila de auditoria e gravá-lo em processados/rotina/. Repita com novo ID para testar
rejeição, que deve mover o resultado para processados/rejeitados/.

No TC02, valide a geração do alerta. Geração ou log não comprovam entrega externa.
Confirme original em recebidos/ e resultado no prefixo esperado. Após reiniciar o
emulador sem remover o volume, o histórico e o original devem continuar disponíveis.

Falha de IA (404, 429, 503, rede ou resposta inválida) deve produzir status="erro" e
erro_extracao, sem classificação clínica concluída. Isso é falha técnica do ensaio,
não aprovação do cenário ambíguo só por ele ter ido para auditoria.

Os PDFs digitalizados de TC01-TC03 contêm apenas imagem, sem camada textual. PNG/JPG
são renderizações dos PDFs digitais. São testes de leitura de documentos impressos;
não comprovam leitura de manuscritos, precisão clínica geral ou conformidade OCI real.
TC03 representa ausência/ilegibilidade explicitamente; não é um desafio real de caligrafia.

Este pacote não executa chamadas Gemini, não envia alertas e não grava dados no app.
Ao processar os documentos, as chamadas ao Gemini podem consumir cota.
'''
    (OUT/'GUIA_TESTES.md').write_text(guia,encoding='utf-8')
    contato=Image.new('RGB',(4*300,2*450),'#e9eef0')
    draw=ImageDraw.Draw(contato)
    for i,(ident,img) in enumerate(previews):
        x,y=(i%4)*300,(i//4)*450
        draw.text((x+12,y+8),ident,fill='#203943')
        contato.paste(img,(x+10,y+30))
    qa=ROOT/'tmp/pdfs'
    qa.mkdir(parents=True,exist_ok=True)
    contato.save(qa/'sinteticos-contato.png')
    pacote=ROOT/'output/mediflow-testes-sinteticos.zip'
    with zipfile.ZipFile(pacote,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file():
                z.write(path,path.relative_to(OUT.parent))
    print(f'Criados {len(CASOS)} casos; {len(list(OUT.rglob("*.pdf")))} PDFs. Pacote: {pacote}')


if __name__=='__main__':
    main()

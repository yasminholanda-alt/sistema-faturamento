import os
import io

import streamlit as st
from pypdf import PdfWriter
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepInFrame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

try:
    import estilo
    TEM_ESTILO = True
except ImportError:
    TEM_ESTILO = False

# ==========================================
# CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gerador de Faturamento Casa Civil | EBM Quintto",
    page_icon="🟡",
    layout="centered"
)

if TEM_ESTILO:
    estilo.aplicar_tema()
    estilo.cabecalho(
        "Gerador de Faturamento - Casa Civil",
        "Preencha os dados abaixo para gerar o dossiê completo de faturamento em PDF único.",
    )
else:
    st.title("Gerador de Faturamento - Casa Civil")
    st.caption("Preencha os dados abaixo para gerar o dossiê completo de faturamento em PDF único.")

NOME_LOGO = "logo ebmquintto preta BG transparente.png"
NOME_ASSINATURA = "assinatura da gabriela martins.jpeg"

# ==========================================
# PADRÃO VISUAL ÚNICO DOS 3 PDFs
# ==========================================
# Troque para True se quiser a carta também em paisagem (mesma orientação das planilhas).
CARTA_PAISAGEM = False

MARGEM = 1.2 * cm                       # mesma margem nas 3 páginas
FRAME_PAD = 6                           # padding interno do frame do ReportLab (pt)
PAGINA_TABELAS = landscape(letter)
PAGINA_CARTA = landscape(letter) if CARTA_PAISAGEM else letter
COR_CABECALHO = colors.HexColor('#D9D9D9')

ASSINATURA_CARTA = (
    "<b>EBM QUINTTO COMUNICAÇÃO LTDA</b><br/>Gabriela Martins - Gerente Financeira"
    "<br/>gabriela.martins@ebmquintto.com.br"
)
ASSINATURA_TABELAS = (
    "<b>Gabriela S. Martins</b><br/>EBM QUINTTO COMUNICAÇÃO LTDA<br/>"
    "Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br"
)


def area_util(pagesize):
    """Largura/altura realmente disponíveis dentro do frame (já descontando margens e padding)."""
    w = pagesize[0] - 2 * MARGEM - 2 * FRAME_PAD - 1
    h = pagesize[1] - 2 * MARGEM - 2 * FRAME_PAD - 1
    return w, h


def montar_pagina(story, pagesize):
    """
    Gera um PDF de UMA página só. Se o conteúdo for maior que a página, o KeepInFrame
    reduz tudo proporcionalmente (vetorial, sem perda de qualidade) em vez de criar página extra.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        rightMargin=MARGEM,
        leftMargin=MARGEM,
        topMargin=MARGEM,
        bottomMargin=MARGEM,
    )
    w, h = area_util(pagesize)
    doc.build([KeepInFrame(w, h, story, mode='shrink')])
    buffer.seek(0)
    return buffer


def imagem(caminho, largura_max, altura_max):
    """Carrega a imagem mantendo a proporção original (sem distorcer)."""
    if not os.path.exists(caminho):
        return None
    w, h = ImageReader(caminho).getSize()
    esc = min(largura_max / w, altura_max / h)
    return Image(caminho, width=w * esc, height=h * esc)


def proporcoes(pesos, total):
    soma = float(sum(pesos))
    return [total * p / soma for p in pesos]


def fabrica_celulas(tam):
    """Cria os estilos/funções de célula para um tamanho de fonte."""
    lead = tam * 1.25
    st_head = ParagraphStyle('CH%s' % tam, fontName='Helvetica-Bold', fontSize=tam, leading=lead, alignment=1)
    st_body = ParagraphStyle('CB%s' % tam, fontName='Helvetica', fontSize=tam, leading=lead, alignment=1)
    st_bold = ParagraphStyle('CBB%s' % tam, fontName='Helvetica-Bold', fontSize=tam, leading=lead, alignment=1)

    def p_h(txt):
        return Paragraph(str(txt), st_head)

    def p_c(txt, b=False):
        return Paragraph(str(txt), st_bold if b else st_body)

    return p_h, p_c, st_head


def estilo_tabela(extra=None):
    base = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]
    return TableStyle(base + (extra or []))


def cabecalho_pagina(largura, titulo_html=None, titulo_style=None):
    """Cabeçalho padrão das 3 páginas: logo à esquerda, título (opcional) ao centro, linha embaixo."""
    logo = imagem(NOME_LOGO, 4.4 * cm, 1.4 * cm)
    col_logo = 5.0 * cm
    celula_titulo = Paragraph(titulo_html, titulo_style) if titulo_html else ''
    t = Table(
        [[logo if logo else '', celula_titulo]],
        colWidths=[col_logo, largura - col_logo],
        rowHeights=[1.9 * cm],
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, 0), 0.8, colors.black),
    ]))
    return t


def bloco_assinatura(texto_html, tam=8):
    """Assinatura no mesmo formato e posição (esquerda) nas 3 páginas."""
    estilo_ass = ParagraphStyle('Ass', fontName='Helvetica', fontSize=tam, leading=tam * 1.3, alignment=0)
    img = imagem(NOME_ASSINATURA, 4.5 * cm, 1.8 * cm)
    linhas = [[img]] if img else []
    linhas.append([Paragraph(texto_html, estilo_ass)])
    t = Table(linhas, colWidths=[8 * cm], hAlign='LEFT')
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


# ==========================================
# CONTRATOS DO CLIENTE
# ==========================================
DESTINATARIO_PADRAO = {
    "orgao": "Casa Civil",
    "att": "Dra. Joelise Collyer Teixeira de Paula",
    "cargo": "Secretária Executiva de Comunicação, Publicidade e Eventos.",
}

CONTRATOS = {
    "C7": {"numero": "177/2024", **DESTINATARIO_PADRAO},
    "C9": {"numero": "125/2023", **DESTINATARIO_PADRAO},
    "CC": {"numero": "125/2023", **DESTINATARIO_PADRAO},
}

def fmt(val: float) -> str:
    return f"{val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# ==========================================
# FORMULÁRIO PRINCIPAL
# ==========================================
with st.form("faturamento_form"):
    col0, col1, col2 = st.columns(3)
    contrato_sel = col0.selectbox(
        "Contrato",
        list(CONTRATOS.keys()),
        format_func=lambda k: f"{k} - {CONTRATOS[k]['numero']}",
    )
    tipo_servico = col1.selectbox(
        "Tipo de Serviço",
        ["Mídia", "Produção", "Custos Internos", "Misto (Terceiros + Custos Internos)"]
    )
    empenho = col2.text_input("Nº do Empenho")

    nup = st.text_input("NUP (Ex: 00000.000000/0000-00)")
    descricao = st.text_area("Descrição do Serviço (Texto da NF)")

    col3, col4 = st.columns(2)
    nf_ebm = col3.text_input("Nº NF EBM")
    data_ebm = col4.text_input("Data Emissão EBM (DD/MM/AAAA)")

    st.markdown("---")
    st.subheader("Dados do Fornecedor / Terceiro")

    fornecedor = st.text_input("Razão Social do Fornecedor / Veículo")
    cnpj_forn = st.text_input("CNPJ do Fornecedor")

    col5, col6 = st.columns(2)
    nf_forn = col5.text_input("Nº NF Fornecedor")
    data_forn = col6.text_input("Data Emissão Fornecedor (DD/MM/AAAA)")

    col7, col8 = st.columns(2)
    doc_cliente = col7.text_input(
        "Nº Doc. Cliente (AP / Plano / OC)",
        help="Documento enviado pela EBM para assinatura do cliente."
    )
    doc_terceiros = col8.text_input(
        "Nº Doc. Terceiros (PP / PI)",
        help="Documento enviado pela EBM para validação da empresa terceirizada/veículo."
    )

    st.markdown("---")
    st.subheader("Tributação e Valores")

    col9, col10 = st.columns(2)
    simples_nacional = col9.radio("Fornecedor Optante do Simples Nacional?", ["SIM", "NÃO"])

    aliq_iss_forn = col10.number_input(
        "% do ISS da Empresa Terceirizada",
        min_value=0.0,
        max_value=10.0,
        value=2.0 if simples_nacional == "NÃO" else 0.0,
        step=0.5,
        help="Alíquota de ISS do município do fornecedor (retido na fonte apenas se NÃO for Simples Nacional)."
    )

    col11, col12 = st.columns(2)
    valor_fornecedor_input = col11.number_input(
        "Valor Bruto da Nota do Fornecedor / Veículo (R$)",
        min_value=0.0,
        step=0.01,
        help="Valor da NF do fornecedor/veículo sobre o qual os honorários serão calculados."
    )

    valor_custo_interno = col12.number_input(
        "Valor de Custos Internos (R$)",
        min_value=0.0,
        step=0.01,
        help="Informe o valor caso haja serviços internos agregados ao processo."
    )

    col13, col14 = st.columns(2)
    valor_bruto_input = col13.number_input(
        "Valor Bruto Total da NF da EBM (Opcional - R$)",
        min_value=0.0,
        step=0.01,
        help="Deixe 0,00 para o sistema calcular automaticamente somando Fornecedor + Honorários + Custos Internos."
    )

    valor_honorarios_manual = col14.number_input(
        "Honorários EBM Manuais (Opcional - R$)",
        min_value=0.0,
        step=0.01,
        help="Deixe 0,00 para calcular automático (18,75% Mídia ou 8% Produção sobre o fornecedor)."
    )

    submit = st.form_submit_button("Gerar PDF Único", use_container_width=True)

# ==========================================
# PROCESSAMENTO DOS DOCUMENTOS
# ==========================================
if submit:
    try:
        contrato = CONTRATOS[contrato_sel]
        numero_contrato = contrato["numero"]

        docs_list = [d.strip() for d in [doc_cliente, doc_terceiros] if d.strip()]
        numero_doc = " / ".join(docs_list) if docs_list else "-"

        is_custos_puros = tipo_servico == "Custos Internos"

        # ----------------------------------------------------
        # CÁLCULO DOS HONORÁRIOS EM CIMA DO FORNECEDOR
        # ----------------------------------------------------
        if is_custos_puros:
            valor_fornecedor = 0.0
            custos_internos_final = valor_custo_interno if valor_custo_interno > 0 else valor_bruto_input
            honorarios_ebm = 0.0
            base_ebm = custos_internos_final
            valor_bruto = custos_internos_final
        else:
            valor_fornecedor = valor_fornecedor_input
            custos_internos_final = valor_custo_interno

            # Se informou honorários manuais, usa o valor; caso contrário, aplica a porcentagem sobre o fornecedor
            if valor_honorarios_manual > 0:
                honorarios_ebm = valor_honorarios_manual
            else:
                if tipo_servico == "Mídia":
                    honorarios_ebm = valor_fornecedor * 0.1875  # 18,75% sobre o fornecedor
                elif tipo_servico in ["Produção", "Misto (Terceiros + Custos Internos)"]:
                    honorarios_ebm = valor_fornecedor * 0.08    # 8,00% sobre o fornecedor
                else:
                    honorarios_ebm = 0.0

            # Base tributável da EBM
            base_ebm = honorarios_ebm + custos_internos_final

            # Valor Bruto Total da NF da EBM
            if valor_bruto_input > 0:
                valor_bruto = valor_bruto_input
            else:
                valor_bruto = valor_fornecedor + honorarios_ebm + custos_internos_final

        # ----------------------------------------------------
        # RETENÇÕES TRIBUTÁRIAS
        # ----------------------------------------------------
        # Fornecedor: 4,8% IRRF + % ISS digitada (apenas se NÃO for Simples)
        if simples_nacional == "SIM" or valor_fornecedor <= 0:
            ret_irrf_forn = 0.0
            ret_iss_forn = 0.0
        else:
            ret_irrf_forn = valor_fornecedor * 0.048
            ret_iss_forn = valor_fornecedor * (aliq_iss_forn / 100.0)

        ret_imp_forn = ret_iss_forn + ret_irrf_forn
        valor_liq_forn = valor_fornecedor - ret_imp_forn

        # EBM QUINTTO: Retém 5% de ISS + 4,8% de IRRF sobre a base própria (Honorários + Custos Internos)
        ret_iss_ebm = base_ebm * 0.05
        ret_irrf_ebm = base_ebm * 0.048
        ret_imp_ebm = ret_iss_ebm + ret_irrf_ebm
        valor_liq_ebm = base_ebm - ret_imp_ebm

        # Consolidação Geral
        valor_liq_total = valor_liq_forn + valor_liq_ebm
        total_iss = ret_iss_ebm + ret_iss_forn
        total_irrf = ret_irrf_ebm + ret_irrf_forn

        # Estilos de texto corrido (carta) e título (planilhas)
        styles = getSampleStyleSheet()
        texto = ParagraphStyle('Texto', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=15)
        texto_bold = ParagraphStyle('TextoBold', parent=texto, fontName='Helvetica-Bold')
        titulo_centro = ParagraphStyle(
            'TituloCentro', parent=texto_bold, fontSize=11, leading=15, alignment=1
        )

        # ------------------------------------------
        # 1. CARTA DE ENCAMINHAMENTO
        # ------------------------------------------
        def gerar_carta_pdf():
            w, _ = area_util(PAGINA_CARTA)
            story = [cabecalho_pagina(w), Spacer(1, 14)]

            story.append(Paragraph(f"Fortaleza, {data_ebm}.", texto))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>À<br/>{contrato['orgao']}</b><br/>Att. {contrato['att']}<br/>{contrato['cargo']}", texto))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Ref. Empenho nº {empenho}", texto_bold))
            story.append(Spacer(1, 12))
            story.append(Paragraph("Prezada Secretária,", texto))
            story.append(Spacer(1, 10))

            if is_custos_puros:
                corpo = f"Segue para pagamento o processo de Custo Interno - EBMQUINTTO.<br/><br/>PAGTO REF. A SERVIÇOS INTERNOS - {descricao} - EBM QUINTTO<br/>CNPJ: 14.470.051/0001-91<br/>OC Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."
            elif tipo_servico == "Mídia":
                corpo = f"Segue para pagamento o processo do Serviço de Mídia.<br/><br/>PAGTO REF. {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."
            elif tipo_servico == "Misto (Terceiros + Custos Internos)":
                corpo = f"Segue para pagamento o processo com Terceirização e Custos Internos agregados.<br/><br/>PAGTO REF. A {descricao}<br/>Fornecedor: {fornecedor} (CNPJ: {cnpj_forn}) e EBM QUINTTO (CNPJ: 14.470.051/0001-91)<br/>Documento Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."
            else:
                corpo = f"Segue para pagamento o processo de Produção.<br/><br/>PAGTO REF. A {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."

            story.append(Paragraph(corpo, texto))
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"Através do contrato nº {numero_contrato}.<br/>Na certeza de contarmos com o parecer favorável.<br/>Subscrevemo-nos,", texto))
            story.append(Spacer(1, 20))
            story.append(bloco_assinatura(ASSINATURA_CARTA, tam=10))

            return montar_pagina(story, PAGINA_CARTA)

        # ------------------------------------------
        # 2. PLANILHA FINANCEIRA (PAISAGEM)
        # ------------------------------------------
        def gerar_financeira_pdf():
            w, _ = area_util(PAGINA_TABELAS)
            p_h, p_c, st_head = fabrica_celulas(8)

            titulo = (
                f"<b>CONTRATO {numero_contrato}</b><br/>"
                f"<b>CONTROLE DE REPASSE - {contrato['orgao'].upper()}</b><br/>"
                f"<b>Nº EMPENHO {empenho}</b><br/>"
                f"<b>NF EBM QUINTTO Nº {nf_ebm}</b><br/>"
                f"<b>.:. EMISSÃO {data_ebm} .:. RECEBIMENTO // .:.</b>"
            )
            story = [cabecalho_pagina(w, titulo, titulo_centro), Spacer(1, 14)]

            nome_identificacao = "EBM QUINTTO" if is_custos_puros else fornecedor
            desc_text = Paragraph(
                f"<b>{numero_doc} - PAGTO REF. {descricao} - {nome_identificacao}</b>", st_head
            )

            headers = [
                p_h("<b>N° EMP</b>"), p_h("<b>NF EBM</b>"), p_h("<b>FORNECEDOR</b>"), p_h("<b>NF FORN.</b>"),
                p_h("<b>VALOR<br/>FORNECEDOR</b>"), p_h("<b>RET. IMP.</b>"), p_h("<b>VALOR LÍQ. FORN.</b>"),
                p_h("<b>HONORÁRIOS EBM</b>"), p_h("<b>SERVIÇOS INTERNOS EBM</b>"), p_h("<b>RET. IMP.</b>"),
                p_h("<b>VALOR LÍQ. EBM</b>"), p_h("<b>VALOR LÍQ NF</b>"), p_h("<b>DATA REPASSE</b>")
            ]

            forn_nome = "SERVIÇOS INTERNOS EBM" if is_custos_puros else fornecedor

            row_data = [
                p_c(empenho), p_c(nf_ebm), p_c(forn_nome), p_c(nf_forn if nf_forn else ''),
                p_c(fmt(valor_fornecedor)), p_c(fmt(ret_imp_forn)), p_c(fmt(valor_liq_forn)),
                p_c(fmt(honorarios_ebm)),
                p_c(fmt(custos_internos_final)),
                p_c(fmt(ret_imp_ebm)), p_c(fmt(valor_liq_ebm)), p_c(fmt(valor_liq_total)), p_c('')
            ]

            row_total = [
                p_c('TOTAL', True), p_c(''), p_c(''), p_c(''),
                p_c(f"R$ {fmt(valor_fornecedor)}", True), p_c(fmt(ret_imp_forn), True), p_c(fmt(valor_liq_forn), True),
                p_c(fmt(honorarios_ebm), True),
                p_c(fmt(custos_internos_final), True),
                p_c(fmt(ret_imp_ebm), True), p_c(fmt(valor_liq_ebm), True), p_c(fmt(valor_liq_total), True), p_c('')
            ]

            col_w = proporcoes(
                [2.0, 1.5, 3.2, 1.5, 2.1, 1.9, 2.1, 2.0, 2.0, 1.9, 2.1, 2.1, 1.6], w
            )

            table_data = [[desc_text] + [''] * 12, headers, row_data, row_total]
            t = Table(table_data, colWidths=col_w)
            t.setStyle(estilo_tabela([
                ('SPAN', (0, 0), (12, 0)),
                ('BACKGROUND', (0, 0), (12, 1), COR_CABECALHO),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
            story.append(bloco_assinatura(ASSINATURA_TABELAS, tam=8))

            return montar_pagina(story, PAGINA_TABELAS)

        # ------------------------------------------
        # 3. DADOS PARA LIQUIDAR (PAISAGEM)
        # ------------------------------------------
        def gerar_liquidar_pdf():
            w, _ = area_util(PAGINA_TABELAS)
            p_h, p_c, _ = fabrica_celulas(10)

            story = [cabecalho_pagina(w, "<b>DADOS PARA LIQUIDAR</b>", titulo_centro), Spacer(1, 14)]

            # Quadro-resumo
            st_lh = ParagraphStyle('LH', parent=texto_bold, fontSize=11, leading=14)
            st_lv = ParagraphStyle('LV', parent=texto, fontSize=11, leading=14, alignment=1)
            p_lh = lambda txt: Paragraph(txt, st_lh)
            p_lv = lambda txt: Paragraph(str(txt), st_lv)

            res_data = [
                [p_lh("EMPENHO"), p_lv(empenho)],
                [p_lh("NUP"), p_lv(nup if nup else '-')],
                [p_lh("VALOR TOTAL"), p_lv(fmt(valor_bruto))],
                [p_lh("RETENÇÃO ISS"), p_lv(fmt(total_iss))],
                [p_lh("RETENÇÃO IRRF"), p_lv(fmt(total_irrf))],
                [p_lh("VALOR LÍQUIDO"), p_lv(fmt(valor_liq_total))]
            ]

            t_res = Table(res_data, colWidths=[5 * cm, 8 * cm], hAlign='LEFT')
            t_res.setStyle(estilo_tabela([
                ('BACKGROUND', (0, 0), (0, -1), COR_CABECALHO),
                ('LEFTPADDING', (0, 0), (0, -1), 6),
            ]))
            story.append(t_res)
            story.append(Spacer(1, 18))

            col_w3 = proporcoes([2.5, 2.2, 3.3, 5.6, 2.2, 2.2, 2.9, 2.4], w)

            # Tabela 1: EBM QUINTTO (ISS 5% + IRRF 4,8%)
            head_ag = [p_h("<b>NF AGÊNCIA</b>"), p_h("<b>DATA EMISSÃO</b>"), p_h("<b>CNPJ</b>"), p_h("<b>RAZÃO SOCIAL</b>"), p_h("<b>ISS (5%)</b>"), p_h("<b>IRRF (4,8%)</b>"), p_h("<b>BASE DE CÁLCULO</b>"), p_h("<b>SIMPLES NACIONAL</b>")]
            row_ag = [p_c(nf_ebm), p_c(data_ebm), p_c("14470051000191"), p_c("EBM QUINTTO COMUNICAÇÃO LTDA"), p_c(fmt(ret_iss_ebm)), p_c(fmt(ret_irrf_ebm)), p_c(fmt(base_ebm)), p_c("NÃO")]
            tot_ag = [p_c("TOTAL", True), p_c(''), p_c(''), p_c(''), p_c(fmt(ret_iss_ebm), True), p_c(fmt(ret_irrf_ebm), True), p_c(fmt(base_ebm), True), p_c('')]

            t_ag = Table([head_ag, row_ag, tot_ag], colWidths=col_w3)
            t_ag.setStyle(estilo_tabela([('BACKGROUND', (0, 0), (-1, 0), COR_CABECALHO)]))
            story.append(t_ag)
            story.append(Spacer(1, 14))

            # Tabela 2: Fornecedor Terceirizado
            lbl_iss_forn = f"ISS ({aliq_iss_forn:.1f}%)" if simples_nacional == "NÃO" and aliq_iss_forn > 0 else "ISS"
            head_fo = [p_h("<b>NF FORNECEDOR</b>"), p_h("<b>DATA EMISSÃO</b>"), p_h("<b>CNPJ</b>"), p_h("<b>RAZÃO SOCIAL</b>"), p_h(f"<b>{lbl_iss_forn}</b>"), p_h("<b>IRRF (4,8%)</b>"), p_h("<b>BASE DE CÁLCULO</b>"), p_h("<b>SIMPLES NACIONAL</b>")]
            row_fo = [p_c(nf_forn if nf_forn else ''), p_c(data_forn if data_forn else ''), p_c(cnpj_forn if cnpj_forn else ''), p_c(fornecedor if fornecedor else ''), p_c(fmt(ret_iss_forn)), p_c(fmt(ret_irrf_forn)), p_c(fmt(valor_fornecedor)), p_c(simples_nacional)]
            tot_fo = [p_c("TOTAL", True), p_c(''), p_c(''), p_c(''), p_c(fmt(ret_iss_forn), True), p_c(fmt(ret_irrf_forn), True), p_c(fmt(valor_fornecedor), True), p_c('')]

            t_fo = Table([head_fo, row_fo, tot_fo], colWidths=col_w3)
            t_fo.setStyle(estilo_tabela([('BACKGROUND', (0, 0), (-1, 0), COR_CABECALHO)]))
            story.append(t_fo)
            story.append(Spacer(1, 20))
            story.append(bloco_assinatura(ASSINATURA_TABELAS, tam=8))

            return montar_pagina(story, PAGINA_TABELAS)

        # ------------------------------------------
        # MESCLAGEM DOS TRÊS DOCUMENTOS
        # ------------------------------------------
        pdf_carta = gerar_carta_pdf()
        pdf_fin = gerar_financeira_pdf()
        pdf_liq = gerar_liquidar_pdf()

        merger = PdfWriter()
        merger.append(pdf_carta)
        merger.append(pdf_fin)
        merger.append(pdf_liq)

        pdf_final_buffer = io.BytesIO()
        merger.write(pdf_final_buffer)
        pdf_final_buffer.seek(0)

        st.success(f"Dossiê gerado com sucesso para o contrato {contrato_sel} ({numero_contrato})!")
        st.download_button(
            label="📄 Baixar Dossiê Completo (BAIXAR)",
            data=pdf_final_buffer.getvalue(),
            file_name=f"Faturamento_CasaCivil_NF{nf_ebm}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        if TEM_ESTILO:
            estilo.rodape()

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o PDF: {e}")

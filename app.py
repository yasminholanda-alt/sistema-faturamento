import os
import io
import zipfile
from datetime import date

import streamlit as st
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

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
        "Preencha os dados abaixo para gerar a carta, a planilha financeira e os dados para liquidar.",
    )
else:
    st.title("Gerador de Faturamento - Casa Civil")
    st.caption("Preencha os dados abaixo para gerar a carta, a planilha financeira e os dados para liquidar.")

NOME_LOGO = "logo ebmquintto preta BG transparente.png"
NOME_ASSINATURA = "assinatura da gabriela martins.jpeg"

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
    tipo_servico = col1.selectbox("Tipo de Serviço", ["Mídia", "Produção", "Custos Internos"])
    empenho = col2.text_input("Nº do Empenho")

    nup = st.text_input("NUP (Ex: 00000.000000/0000-00)")
    descricao = st.text_area("Descrição do Serviço (Texto da NF)")

    col3, col4 = st.columns(2)
    nf_ebm = col3.text_input("Nº NF EBM")
    data_ebm = col4.text_input("Data Emissão EBM (DD/MM/AAAA)")

    fornecedor = st.text_input("Razão Social do Fornecedor / Veículo")
    cnpj_forn = st.text_input("CNPJ do Fornecedor")

    col5, col6 = st.columns(2)
    nf_forn = col5.text_input("Nº NF Fornecedor")
    data_forn = col6.text_input("Data Emissão Fornecedor (DD/MM/AAAA)")

    col7, col8 = st.columns(2)
    numero_doc = col7.text_input("Nº do Documento (OC / PI / AP / PP / Plano)")
    simples_nacional = col8.radio("Fornecedor Optante do Simples Nacional?", ["SIM", "NÃO"])

    col9, col10 = st.columns(2)
    valor_bruto = col9.number_input("Valor Bruto Total da NF (R\$)", min_value=0.0, step=0.01)
    valor_fornecedor = col10.number_input("Valor Repassado ao Fornecedor (R\$)", min_value=0.0, step=0.01)

    submit = st.form_submit_button("Gerar 3 PDFs", use_container_width=True)

# ==========================================
# PROCESSAMENTO APÓS SUBMISSÃO
# ==========================================
if submit:
    try:
        contrato = CONTRATOS[contrato_sel]
        numero_contrato = contrato["numero"]

        # Cálculos Financeiros
        honorarios_ebm = valor_bruto - valor_fornecedor

        if simples_nacional == "SIM":
            ret_iss_forn = 0.0
            ret_irrf_forn = 0.0
        else:
            ret_iss_forn = valor_fornecedor * 0.02
            ret_irrf_forn = valor_fornecedor * 0.048

        ret_imp_forn = ret_iss_forn + ret_irrf_forn
        valor_liq_forn = valor_fornecedor - ret_imp_forn

        ret_iss_ebm = honorarios_ebm * 0.05
        ret_irrf_ebm = honorarios_ebm * 0.048
        ret_imp_ebm = ret_iss_ebm + ret_irrf_ebm
        valor_liq_ebm = honorarios_ebm - ret_imp_ebm

        valor_liq_total = valor_liq_forn + valor_liq_ebm
        total_iss = ret_iss_ebm + ret_iss_forn
        total_irrf = ret_irrf_ebm + ret_irrf_forn

        # Estilos de Parágrafo
        styles = getSampleStyleSheet()
        normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
        bold = ParagraphStyle('BoldCustom', parent=normal, fontName='Helvetica-Bold')
        title_center = ParagraphStyle('TitleCenter', parent=normal, fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1)

        cell_head = ParagraphStyle('CHead', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1)
        cell_body = ParagraphStyle('CBody', fontName='Helvetica', fontSize=6.5, leading=8, alignment=1)
        cell_body_bold = ParagraphStyle('CBodyBold', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1)

        def p_h(txt): return Paragraph(f"<b>{txt}</b>", cell_head)
        def p_c(txt, b=False): return Paragraph(str(txt), cell_body_bold if b else cell_body)

        # 1. CARTA DE ENCAMINHAMENTO
        def gerar_carta_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []

            if os.path.exists(NOME_LOGO):
                story.append(Image(NOME_LOGO, width=3.8*cm, height=1.1*cm))
                story.append(Spacer(1, 15))

            story.append(Paragraph(f"Fortaleza, {data_ebm}.", normal))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>À<br/>{contrato['orgao']}</b><br/>Att. {contrato['att']}<br/>{contrato['cargo']}", normal))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Ref. Empenho nº {empenho}</b>", bold))
            story.append(Spacer(1, 12))
            story.append(Paragraph("Prezada Secretária,", normal))
            story.append(Spacer(1, 10))

            if tipo_servico == "Custos Internos":
                texto = f"Segue para pagamento o processo de Custo Interno - EBMQUINTTO.<br/><br/>PAGTO REF. A SERVIÇOS INTERNOS - {descricao} - EBM QUINTTO<br/>CNPJ: 14.470.051/0001-91<br/>OC Nº {numero_doc} no valor de <b>R\$ {fmt(valor_bruto)}</b>."
            elif tipo_servico == "Mídia":
                texto = f"Segue para pagamento o processo do Serviço de Mídia.<br/><br/>PAGTO REF. {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R\$ {fmt(valor_bruto)}</b>."
            else:
                texto = f"Segue para pagamento o processo de Produção.<br/><br/>PAGTO REF. A {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R\$ {fmt(valor_bruto)}</b>."

            story.append(Paragraph(texto, normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"Através do contrato nº {numero_contrato}.<br/>Na certeza de contarmos com o parecer favorável.<br/>Subscrevemo-nos,", normal))
            story.append(Spacer(1, 20))

            if os.path.exists(NOME_ASSINATURA):
                story.append(Image(NOME_ASSINATURA, width=4*cm, height=1.8*cm))
            story.append(Paragraph("<b>EBM QUINTTO COMUNICAÇÃO LTDA</b><br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br", normal))

            doc.build(story)
            return buffer.getvalue()

        # 2. PLANILHA FINANCEIRA
        def gerar_financeira_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
            story = []

            p_header_text = Paragraph(f"""
            <b>CONTRATO {numero_contrato}</b><br/>
            <b>CONTROLE DE REPASSE - {contrato['orgao'].upper()}</b><br/>
            <b>Nº EMPENHO {empenho}</b><br/>
            <b>NF EBM QUINTTO Nº {nf_ebm}</b><br/>
            <b>.:. EMISSÃO {data_ebm} .:. RECEBIMENTO // .:.</b>
            """, title_center)

            if os.path.exists(NOME_LOGO):
                img_logo = Image(NOME_LOGO, width=3.8*cm, height=1.1*cm)
                h_table = Table([[img_logo, p_header_text]], colWidths=[4*cm, 21.5*cm])
                h_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,0), 'LEFT')]))
                story.append(h_table)
            else:
                story.append(p_header_text)

            story.append(Spacer(1, 10))

            desc_text = Paragraph(f"<b>{numero_doc} - PAGTO REF. {descricao} - {fornecedor if tipo_servico != 'Custos Internos' else 'EBM QUINTTO'}</b>", cell_head)

            headers = [
                p_h("N° EMP"), p_h("NF EBM"), p_h("FORNECEDOR"), p_h("NF FORN."),
                p_h("VALOR<br/>FORNECEDOR"), p_h("RET. IMP."), p_h("VALOR LÍQ. FORN."),
                p_h("HONORÁRIOS EBM"), p_h("SERVIÇOS INTERNOS EBM"), p_h("RET. IMP."),
                p_h("VALOR LÍQ. EBM"), p_h("VALOR LÍQ NF"), p_h("DATA REPASSE")
            ]

            is_custos = tipo_servico == "Custos Internos"
            forn_nome = "SERVIÇOS INTERNOS EBM" if is_custos else fornecedor

            row_data = [
                p_c(empenho), p_c(nf_ebm), p_c(forn_nome), p_c(nf_forn if nf_forn else ''),
                p_c(fmt(valor_fornecedor)), p_c(fmt(ret_imp_forn)), p_c(fmt(valor_liq_forn)),
                p_c(fmt(0.0) if is_custos else fmt(honorarios_ebm)),
                p_c(fmt(honorarios_ebm) if is_custos else fmt(0.0)),
                p_c(fmt(ret_imp_ebm)), p_c(fmt(valor_liq_ebm)), p_c(fmt(valor_liq_total)), p_c('')
            ]

            row_total = [
                p_c('TOTAL', True), p_c(''), p_c(''), p_c(''),
                p_c(f"R\$ {fmt(valor_fornecedor)}", True), p_c(fmt(ret_imp_forn), True), p_c(fmt(valor_liq_forn), True),
                p_c(fmt(0.0) if is_custos else fmt(honorarios_ebm), True),
                p_c(fmt(honorarios_ebm) if is_custos else fmt(0.0), True),
                p_c(fmt(ret_imp_ebm), True), p_c(fmt(valor_liq_ebm), True), p_c(fmt(valor_liq_total), True), p_c('')
            ]

            col_w = [1.4*cm, 1.4*cm, 4.5*cm, 1.4*cm, 2.2*cm, 1.6*cm, 2.2*cm, 2.1*cm, 2.1*cm, 1.6*cm, 2.1*cm, 2.2*cm, 1.8*cm]

            table_data = [[desc_text] + ['']*12, headers, row_data, row_total]
            t = Table(table_data, colWidths=col_w)
            t.setStyle(TableStyle([
                ('SPAN', (0,0), (12,0)),
                ('BACKGROUND', (0,0), (12,1), colors.HexColor('#D9D9D9')),
                ('ALIGN', (0,

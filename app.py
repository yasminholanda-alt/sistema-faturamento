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
# CONFIGURAÇÕES E ESTILO
# ==========================================
st.set_page_config(
    page_title="Gerador de Faturamento Casa Civil | EBM Quintto",
    page_icon="🟡",
    layout="wide"
)

if TEM_ESTILO:
    estilo.aplicar_tema()
    estilo.cabecalho(
        "Gerador de Faturamento - Casa Civil",
        "Gere a carta, a planilha de repasse e o espelho de liquidação padronizados.",
    )
else:
    st.title("Gerador de Faturamento - Casa Civil")
    st.caption("EBM Quintto Comunicação LTDA")

NOME_LOGO = "logo ebmquintto preta BG transparente.png"
NOME_ASSINATURA = "assinatura da gabriela martins.jpeg"

# ==========================================
# CONTRATOS DO CLIENTE
# ==========================================
DESTINATARIO_PADRAO = {
    "orgao": "Casa Civil do Estado do Ceará",
    "att": "Dra. Joelise Collyer Teixeira de Paula",
    "cargo": "Secretária Executiva de Comunicação, Publicidade e Eventos",
}

CONTRATOS = {
    "C7": {"numero": "177/2024", **DESTINATARIO_PADRAO},
    "C9": {"numero": "125/2023", **DESTINATARIO_PADRAO},
    "CC": {"numero": "125/2023", **DESTINATARIO_PADRAO},
}

def fmt(val: float) -> str:
    """Formata valor monetário no padrão brasileiro: 1.234,56"""
    return f"{val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def formatar_cnpj(v: str) -> str:
    nums = "".join(filter(str.isdigit, v))
    if len(nums) == 14:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:]}"
    return v

# ==========================================
# FORMULÁRIO DE ENTRADA
# ==========================================
with st.form("faturamento_form"):
    st.subheader("1. Identificação do Processo")
    col0, col1, col2 = st.columns(3)
    contrato_sel = col0.selectbox(
        "Contrato",
        list(CONTRATOS.keys()),
        format_func=lambda k: f"{k} - Contrato nº {CONTRATOS[k]['numero']}",
    )
    tipo_servico = col1.selectbox("Tipo de Serviço", ["Mídia", "Produção", "Custos Internos"])
    empenho = col2.text_input("Nº do Empenho", placeholder="Ex: 2026NE00123")

    col_nup, col_doc = st.columns([2, 1])
    nup = col_nup.text_input("NUP / Processo SEI", placeholder="Ex: 00000.000000/2026-00")
    numero_doc = col_doc.text_input("Nº do Documento (OC / PI / AP / PP / Plano)")

    descricao = st.text_area("Descrição do Serviço (Texto da NF)", placeholder="Ex: VEICULAÇÃO DE CAMPANHA INSTITUCIONAL...")

    st.markdown("---")
    st.subheader("2. Faturamento Agência (EBM Quintto)")
    col_nf_ebm, col_data_ebm = st.columns(2)
    nf_ebm = col_nf_ebm.text_input("Nº NF EBM")
    data_ebm = col_data_ebm.date_input("Data de Emissão da NF EBM", value=date.today())

    st.markdown("---")
    st.subheader("3. Dados do Fornecedor / Terceiro")
    if tipo_servico == "Custos Internos":
        st.info("💡 Modo 'Custos Internos' selecionado: o valor total é faturado diretamente como serviço próprio da agência.")
        fornecedor = "EBM QUINTTO COMUNICAÇÃO LTDA"
        cnpj_forn = "14.470.051/0001-91"
        nf_forn = ""
        data_forn = None
        simples_nacional = "NÃO"
    else:
        col_forn_1, col_forn_2 = st.columns([2, 1])
        fornecedor = col_forn_1.text_input("Razão Social do Fornecedor / Veículo")
        cnpj_forn = formatar_cnpj(col_forn_2.text_input("CNPJ do Fornecedor"))

        col_fnf_1, col_fnf_2, col_fnf_3 = st.columns([1, 1, 1])
        nf_forn = col_fnf_1.text_input("Nº NF Fornecedor")
        data_forn = col_fnf_2.date_input("Data Emissão Fornecedor", value=date.today())
        simples_nacional = col_fnf_3.radio("Optante Simples Nacional?", ["NÃO", "SIM"], horizontal=True)

    st.markdown("---")
    st.subheader("4. Valores e Retenções")
    col_v1, col_v2 = st.columns(2)
    valor_bruto = col_v1.number_input("Valor Bruto Total da NF (R\$)", min_value=0.0, step=10.0, format="%.2f")
    valor_fornecedor = col_v2.number_input(
        "Valor Repassado ao Fornecedor (R\$)",
        min_value=0.0,
        max_value=float(valor_bruto),
        value=0.0 if tipo_servico == "Custos Internos" else 0.0,
        disabled=(tipo_servico == "Custos Internos"),
        step=10.0,
        format="%.2f"
    )

    with st.expander("⚙️ Ajuste de Alíquotas de Imposto (Padrão: 5% ISS EBM, 2% ISS Fornecedor, 4,8% IRRF)"):
        c_aliq1, c_aliq2, c_aliq3 = st.columns(3)
        aliq_iss_ebm = c_aliq1.number_input("Alíquota ISS EBM (%)", value=5.0, step=0.5) / 100.0
        aliq_irrf_ebm = c_aliq2.number_input("Alíquota IRRF EBM (%)", value=4.8, step=0.1) / 100.0
        aliq_iss_forn = c_aliq3.number_input("Alíquota ISS Fornecedor (%)", value=2.0, step=0.5) / 100.0

    submit = st.form_submit_button("📄 Gerar Relatórios e Documentos", use_container_width=True)

# ==========================================
# PROCESSAMENTO E GERAÇÃO
# ==========================================
if submit:
    # Validações primárias
    erros = []
    if not empenho.strip():
        erros.append("O campo 'Nº do Empenho' é obrigatório.")
    if not nf_ebm.strip():
        erros.append("O campo 'Nº NF EBM' é obrigatório.")
    if valor_bruto <= 0:
        erros.append("O 'Valor Bruto Total' deve ser maior que zero.")
    if tipo_servico != "Custos Internos" and not fornecedor.strip():
        erros.append("A 'Razão Social do Fornecedor' é obrigatória para serviços de Mídia e Produção.")

    if erros:
        for err in erros:
            st.error(err)
    else:
        try:
            contrato = CONTRATOS[contrato_sel]
            numero_contrato = contrato["numero"]
            data_ebm_str = data_ebm.strftime("%d/%m/%Y")
            data_forn_str = data_forn.strftime("%d/%m/%Y") if data_forn else ""

            # Cálculos da Agência
            if tipo_servico == "Custos Internos":
                valor_fornecedor = 0.0
                honorarios_ebm = valor_bruto
            else:
                honorarios_ebm = max(0.0, valor_bruto - valor_fornecedor)

            # Impostos Fornecedor
            if simples_nacional == "SIM" or tipo_servico == "Custos Internos":
                ret_iss_forn = 0.0
                ret_irrf_forn = 0.0
            else:
                ret_iss_forn = valor_fornecedor * aliq_iss_forn
                ret_irrf_forn = valor_fornecedor * 0.048

            ret_imp_forn = ret_iss_forn + ret_irrf_forn
            valor_liq_forn = valor_fornecedor - ret_imp_forn

            # Impostos EBM
            ret_iss_ebm = honorarios_ebm * aliq_iss_ebm
            ret_irrf_ebm = honorarios_ebm * aliq_irrf_ebm
            ret_imp_ebm = ret_iss_ebm + ret_irrf_ebm
            valor_liq_ebm = honorarios_ebm - ret_imp_ebm

            valor_liq_total = valor_liq_forn + valor_liq_ebm
            total_iss = ret_iss_ebm + ret_iss_forn
            total_irrf = ret_irrf_ebm + ret_irrf_forn

            # Estilos de parágrafo ReportLab
            styles = getSampleStyleSheet()
            normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11)
            bold = ParagraphStyle('BoldCustom', parent=normal, fontName='Helvetica-Bold')
            title_center = ParagraphStyle('TitleCenter', parent=normal, fontName='Helvetica-Bold', fontSize=8.5, leading=12, alignment=1)
            cell_head = ParagraphStyle('CHead', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1)
            cell_body = ParagraphStyle('CBody', fontName='Helvetica', fontSize=6.5, leading=8, alignment=1)
            cell_body_bold = ParagraphStyle('CBodyBold', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1)

            def p_h(txt): return Paragraph(f"<b>{txt}</b>", cell_head)
            def p_c(txt, b=False): return Paragraph(str(txt), cell_body_bold if b else cell_body)

            # ------------------------------------------
            # PDF 1: CARTA
            # ------------------------------------------
            def gerar_carta_pdf():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
                story = []

                if os.path.exists(NOME_LOGO):
                    story.append(Image(NOME_LOGO, width=3.8*cm, height=1.1*cm))
                    story.append(Spacer(1, 15))

                story.append(Paragraph(f"Fortaleza, {data_ebm_str}.", normal))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"<b>À<br/>{contrato['orgao']}</b><br/>Att. {contrato['att']}<br/>{contrato['cargo']}", normal))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"<b>Ref. Empenho nº {empenho}</b> | NUP: {nup if nup else 'Não informado'}", bold))
                story.append(Spacer(1, 12))
                story.append(Paragraph("Prezada Secretária,", normal))
                story.append(Spacer(1, 10))

                if tipo_servico == "Custos Internos":
                    texto = f"Segue para pagamento o processo de Custo Interno - EBMQUINTTO.<br/><br/>PAGTO REF. A SERVIÇOS INTERNOS - {descricao} - EBM QUINTTO<br/>CNPJ: 14.470.051/0001-91<br/>Documento Nº {numero_doc} no valor de <b>R\$ {fmt(valor_bruto)}</b>."
                elif tipo_servico == "Mídia":
                    texto = f"Segue para pagamento o processo do Serviço de Mídia.<br/><br/>PAGTO REF. {descricao}<br/>Fornecedor: {fornecedor}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R\$ {fmt(valor_bruto)}</b>."
                else:
                    texto = f"Segue para pagamento o processo de Produção.<br/><br/>PAGTO REF. A {descricao}<br/>Fornecedor: {fornecedor}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R\$ {fmt(valor_bruto)}</b>."

                story.append(Paragraph(texto, normal))
                story.append(Spacer(1, 15))
                story.append(Paragraph(f"Através do contrato nº {numero_contrato}.<br/>Na certeza de contarmos com o parecer favorável.<br/>Subscrevemo-nos,", normal))
                story.append(Spacer(1, 20))

                if os.path.exists(NOME_ASSINATURA):
                    story.append(Image(NOME_ASSINATURA, width=4*cm, height=1.8*cm))
                story.append(Paragraph("<b>EBM QUINTTO COMUNICAÇÃO LTDA</b><br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br", normal))

                doc.build(story)
                return buffer.getvalue()

            # ------------------------------------------
            # PDF 2: PLANILHA FINANCEIRA
            # ------------------------------------------
            def gerar_financeira_pdf():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
                story = []

                p_header_text = Paragraph(f"""
                <b>CONTRATO {numero_contrato}</b><br/>
                <b>CONTROLE DE REPASSE - {contrato['orgao'].upper()}</b><br/>
                <b>Nº EMPENHO {empenho}</b> | <b>NF EBM QUINTTO Nº {nf_ebm}</b><br/>
                <b>.:. EMISSÃO {data_ebm_str} .:. RECEBIMENTO // .:.</b>
                """, title_center)

                if os.path.exists(NOME_LOGO):
                    img_logo = Image(NOME_LOGO, width=3.8*cm, height=1.1*cm)
                    h_table = Table([[img_logo, p_header_text]], colWidths=[4*cm, 21.5*cm])
                    h_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,0), 'LEFT')]))
                    story.append(h_table)
                else:
                    story.append(p_header_text)

                story.append(Spacer(1, 10))

                desc_text = Paragraph(f"<b>{numero_doc} - PAGTO REF. {descricao} - {fornecedor}</b>", cell_head)
                headers = [
                    p_h("N° EMP"), p_h("NF EBM"), p_h("FORNECEDOR"), p_h("NF FORN."),
                    p_h("VALOR<br/>FORNECEDOR"), p_h("RET. IMP."), p_h("VALOR LÍQ.<br/>FORN."),
                    p_h("HONORÁRIOS<br/>EBM"), p_h("SERVIÇOS<br/>INTERNOS"), p_h("RET. IMP.<br/>EBM"),
                    p_h("VALOR LÍQ.<br/>EBM"), p_h("VALOR LÍQ.<br/>NF TOTAL"), p_h("DATA<br/>REPASSE")
                ]

                is_custos = tipo_servico == "Custos Internos"
                row_data = [
                    p_c(empenho), p_c(nf_ebm), p_c(fornecedor), p_c(nf_forn if nf_forn else '-'),
                    p_c(fmt(valor_fornecedor)), p_c(fmt(ret_imp_forn)), p_c(fmt(valor_liq_forn)),
                    p_c(fmt(0.0) if is_custos else fmt(honorarios_ebm)),
                    p_c(fmt(honorarios_ebm) if is_custos else fmt(0.0)),
                    p_c(fmt(ret_imp_ebm)), p_c(fmt(valor_liq_ebm)), p_c(fmt(valor_liq_total)), p_c('-')
                ]

                row_total = [
                    p_c('TOTAL', True), p_c(''), p_c(''), p_c(''),
                    p_c(f"R\$ {fmt(valor_fornecedor)}", True), p_c(fmt(ret_imp_forn), True), p_c(fmt(valor_liq_forn), True),
                    p_c(fmt(0.0) if is_custos else fmt(honorarios_ebm), True),
                    p_c(fmt(honorarios_ebm) if is_custos else fmt(0.0), True),
                    p_c(fmt(ret_imp_ebm), True), p_c(fmt(valor_liq_ebm), True), p_c(fmt(valor_liq_total), True), p_c('')
                ]

                col_w = [1.4*cm, 1.4*cm, 4.5*cm, 1.4*cm, 2.2*cm, 1.6*cm, 2.2*cm, 2.1*cm, 2.1*cm, 1.6*cm, 2.1*cm, 2.2*cm, 1.8*cm]
                t = Table([[desc_text] + ['']*12, headers, row_data, row_total], colWidths=col_w)
                t.setStyle(TableStyle([
                    ('SPAN', (0,0), (12,0)),
                    ('BACKGROUND', (0,0), (12,1), colors.HexColor('#D9D9D9')),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]))
                story.append(t)
                story.append(Spacer(1, 15))

                if os.path.exists(NOME_ASSINATURA):
                    img_ass = Image(NOME_ASSINATURA, width=3.5*cm, height=1.4*cm)
                    p_ass_txt = Paragraph("<b>Gabriela S. Martins</b><br/><font size=5>EBM QUINTTO COMUNICAÇÃO LTDA<br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br</font>", cell_body)
                    ass_box = Table([[img_ass], [p_ass_txt]], colWidths=[4.5*cm])
                    ass_box.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                    layout_ass = Table([['', ass_box]], colWidths=[21*cm, 4.5*cm])
                    story.append(layout_ass)

                doc.build(story)
                return buffer.getvalue()

            # ------------------------------------------
            # PDF 3: DADOS PARA LIQUIDAR
            # ------------------------------------------
            def gerar_liquidar_pdf():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
                story = []

                p_lh = lambda txt: Paragraph(f"<b>{txt}</b>", ParagraphStyle('LH', parent=normal, fontSize=7, fontName='Helvetica-Bold'))
                p_lv = lambda txt: Paragraph(str(txt), ParagraphStyle('LV', parent=normal, fontSize=7, alignment=1))

                res_data = [
                    [p_lh("EMPENHO"), p_lv(empenho)],
                    [p_lh("NUP"), p_lv(nup if nup else '-')],
                    [p_lh("VALOR TOTAL"), p_lv(fmt(valor_bruto))],
                    [p_lh("RETENÇÃO ISS"), p_lv(fmt(total_iss))],
                    [p_lh("RETENÇÃO IRRF"), p_lv(fmt(total_irrf))],
                    [p_lh("VALOR LÍQUIDO"), p_lv(fmt(valor_liq_total))]
                ]

                t_res = Table(res_data, colWidths=[3.2*cm, 4.5*cm])
                t_res.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#D9D9D9')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 2),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))

                story.append(Table([[t_res, '']], colWidths=[8*cm, 17.5*cm]))
                story.append(Spacer(1, 15))

                col_w3 = [2.5*cm, 2.2*cm, 3.2*cm, 7.0*cm, 1.8*cm, 1.8*cm, 2.7*cm, 2.3*cm]

                # Tabela EBM
                head_ag = [p_h("NF AGÊNCIA"), p_h("DATA EMISSÃO"), p_h("CNPJ"), p_h("RAZÃO SOCIAL"), p_h("ISS"), p_h("IRRF"), p_h("BASE DE CÁLCULO"), p_h("SIMPLES NACIONAL")]
                row_ag = [p_c(nf_ebm), p_c(data_ebm_str), p_c("14.470.051/0001-91"), p_c("EBM QUINTTO COMUNICAÇÃO LTDA"), p_c(fmt(ret_iss_ebm)), p_c(fmt(ret_irrf_ebm)), p_c(fmt(honorarios_ebm)), p_c("NÃO")]
                tot_ag = [p_c("TOTAL", True), p_c(''), p_c(''), p_c(''), p_c(fmt(ret_iss_ebm), True), p_c(fmt(ret_irrf_ebm), True), p_c(fmt(honorarios_ebm), True), p_c('')]

                t_ag = Table([head_ag, row_ag, tot_ag], colWidths=col_w3)
                t_ag.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D9D9D9')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]))
                story.append(t_ag.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D9D9D9')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
])) # <-- Veja se tem o colchete ']' e os dois parênteses '))'

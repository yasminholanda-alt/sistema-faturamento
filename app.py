import os
import io
import zipfile

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
# PROCESSAMENTO DOS DOCUMENTOS
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
        total_iss = ret_iss_ebm + ret_iss_

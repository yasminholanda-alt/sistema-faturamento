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
# CONFIGURAÇÕES E TEMA
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
        "Preencha os dados abaixo para gerar a carta, a planilha financeira e os dados para liquidar.",
    )
else:
    st.title("Gerador de Faturamento - Casa Civil")
    st.caption("EBM Quintto Comunicação LTDA")

NOME_LOGO = "logo ebmquintto preta BG transparente.png"
NOME_ASSINATURA = "assinatura da gabriela martins.jpeg"

# ==========================================
# CONTRATOS DO CLIENTE (Casa Civil - Ceará)
# ==========================================
DESTINATARIO_PADRAO = {
    "orgao": "Casa Civil do Estado do Ceará",
    "att": "Dra. Joelise Collyer Teixeira de Paula",
    "cargo": "Secretária Executiva de Comunicação, Publicidade e Eventos.",
}

CONTRATOS = {
    "C7": {"numero": "177/2024", **DESTINATARIO_PADRAO},
    "C9": {"numero": "125/2023", **DESTINATARIO_PADRAO},
    "CC": {"numero": "125/2023", **DESTINATARIO_PADRAO},
}

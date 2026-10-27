"""Identidade visual da EBM Quintto para o app Streamlit.

Cores e fontes seguem o manual de identidade visual:
  Amarelo #FFC20E (Pantone 123c) | Preto #231F20 (Black 7c)
  Cinza   #414042 (Pantone 4287c) | Oliva #403D1F (Pantone 448c)
  Fontes de apoio: Prompt (títulos) e Source Code Pro (texto).

Este arquivo não chama nada do Streamlit ao ser importado, então pode ser
importado antes do st.set_page_config.
"""
from functools import lru_cache
from pathlib import Path
import base64

import streamlit as st

LOGO_PATH = Path(__file__).parent / "logo ebmquintto preta BG transparente.png"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@500;700;800&family=Source+Code+Pro:wght@400;600&display=swap');

:root {
  --amarelo: #FFC20E;
  --preto: #231F20;
  --cinza: #414042;
  --oliva: #403D1F;
}

/* Layout geral */
.block-container { max-width: 880px; padding-top: 1.5rem; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* Faixa diagonal no topo (referência ao padrão de listras da marca) */
.faixa {
  height: 10px;
  border: 1px solid var(--cinza);
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  background: repeating-linear-gradient(-45deg,
      var(--amarelo) 0 12px, var(--preto) 12px 24px);
}

/* Cabeçalho amarelo com logo */
.cabecalho {
  background: var(--amarelo);
  color: var(--preto);
  border-radius: 0 0 10px 10px;
  padding: 22px 28px;
  display: flex;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}
.cabecalho img { height: 46px; width: auto; }
.cabecalho .nome-marca {
  font-family: 'Prompt', sans-serif; font-weight: 800; font-size: 1.6rem;
}
.cabecalho .textos {
  border-left: 3px solid var(--preto);
  padding-left: 24px;
  flex: 1;
  min-width: 240px;
}
.cabecalho .titulo {
  font-family: 'Prompt', sans-serif; font-weight: 800;
  font-size: 1.55rem; line-height: 1.15; color: var(--preto);
}
.cabecalho p { margin: 6px 0 0; font-size: 0.85rem; color: var(--preto); }

/* Títulos de seção dentro do formulário */
.secao {
  font-family: 'Prompt', sans-serif; font-weight: 700; font-size: 1.05rem;
  color: var(--amarelo);
  border-left: 4px solid var(--amarelo);
  padding-left: 10px;
  margin: 26px 0 10px;
}

/* Formulário */
[data-testid="stForm"] {
  border: 1px solid var(--cinza);
  border-radius: 10px;
  padding: 4px 24px 24px;
  background: transparent;
}

/* Botões no amarelo da marca */
.stButton button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button {
  background: var(--amarelo) !important;
  color: var(--preto) !important;
  border: none !important;
  border-radius: 6px;
  font-weight: 700;
}
.stButton button p,
[data-testid="stFormSubmitButton"] button p,
[data-testid="stDownloadButton"] button p {
  color: var(--preto) !important; font-weight: 700;
}
.stButton button:hover,
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stDownloadButton"] button:hover {
  background: #FFFFFF !important;
}

/* Rodapé */
.rodape {
  margin-top: 40px; padding-top: 16px;
  border-top: 1px solid var(--cinza);
  font-size: 0.75rem; line-height: 1.6;
  color: rgba(255, 255, 255, 0.65);
}
.rodape b { color: var(--amarelo); }
</style>
"""


@lru_cache(maxsize=1)
def _logo_html():
    """Logo em base64 (para ficar dentro do HTML). Se faltar, mostra o nome."""
    try:
        dados = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{dados}" alt="EBM Quintto">'
    except OSError:
        return '<span class="nome-marca">EBMQUINTTO.</span>'


def aplicar_tema():
    """Injeta fontes e CSS. Chamar logo depois do st.set_page_config."""
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(titulo, subtitulo=""):
    """Faixa de listras + cabeçalho amarelo com o logo e o título."""
    st.markdown('<div class="faixa"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="cabecalho">{_logo_html()}'
        f'<div class="textos"><div class="titulo">{titulo}</div>'
        f'<p>{subtitulo}</p></div></div>',
        unsafe_allow_html=True,
    )


def secao(texto):
    """Título de seção (use dentro do formulário para agrupar campos)."""
    st.markdown(f'<div class="secao">{texto}</div>', unsafe_allow_html=True)


def rodape():
    """Rodapé institucional. Chamar no fim do app.py."""
    st.markdown(
        '<div class="rodape"><b>EBM Quintto Comunicação Ltda</b><br>'
        'R. Beni Carvalho, 130 - 60135-400, Fortaleza/CE<br>'
        'ebmquintto.com.br<br>Fora da curva, direto ao ponto.</div>',
        unsafe_allow_html=True,
    )

import streamlit as st
import openpyxl
import base64
import io
import zipfile

st.set_page_config(page_title="Faturamento EBM Quintto", layout="centered")

st.title("📊 Gerador de Faturamento - EBM Quintto")
st.write("Preencha os dados da Nota Fiscal abaixo para gerar os documentos de faturamento.")

with st.form("faturamento_form"):
    col1, col2 = st.columns(2)
    tipo = col1.selectbox("Tipo de Serviço", ["Mídia", "Produção", "Custos Internos"])
    empenho = col2.text_input("Nº do Empenho")
    
    nup = st.text_input("NUP (Ex: 30001.008502/2026-87)")
    descricao = st.text_area("Descrição do Serviço / PI / Plano")
    
    col3, col4 = st.columns(2)
    nf_ebm = col3.text_input("Nº NF EBM")
    data_ebm = col4.text_input("Data Emissão EBM (DD/MM/AAAA)")
    
    fornecedor = st.text_input("Razão Social do Fornecedor / Veículo")
    cnpj_forn = st.text_input("CNPJ do Fornecedor")
    
    col5, col6 = st.columns(2)
    nf_forn = col5.text_input("Nº NF Fornecedor")
    data_forn = col6.text_input("Data Emissão Fornecedor (DD/MM/AAAA)")
    
    col7, col8 = st.columns(2)
    valor_bruto = col7.number_input("Valor Bruto Total da NF (R$)", min_value=0.0, step=0.01)
    valor_fornecedor = col8.number_input("Valor Repassado ao Fornecedor (R$)", min_value=0.0, step=0.01)
    
    simples_nacional = st.radio("O Fornecedor é optante do Simples Nacional?", ["SIM", "NÃO"])
    
    submit = st.form_submit_button("Gerar Documentos")

if submit:
    try:
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
        
        valor_liq_nf = valor_liq_forn + valor_liq_ebm

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            wb_liq = openpyxl.load_workbook("17_PLANILHA DADOS PARA LIQUIDAR.xlsx")
            sheet_liq = wb_liq.active
            sheet_liq["B1"], sheet_liq["B2"], sheet_liq["B3"] = empenho, nup, valor_bruto
            sheet_liq["B4"], sheet_liq["B5"], sheet_liq["B6"] = (ret_iss_ebm + ret_iss_forn), (ret_irrf_ebm + ret_irrf_forn), valor_liq_nf
            
            sheet_liq["A9"], sheet_liq["B9"], sheet_liq["E9"], sheet_liq["F9"], sheet_liq["G9"] = nf_ebm, data_ebm, ret_iss_ebm, ret_irrf_ebm, honorarios_ebm
            sheet_liq["A13"], sheet_liq["B13"], sheet_liq["C13"], sheet_liq["D13"] = nf_forn, data_forn, cnpj_forn, fornecedor
            sheet_liq["E13"], sheet_liq["F13"], sheet_liq["G13"], sheet_liq["H13"] = ret_iss_forn, ret_irrf_forn, valor_fornecedor, simples_nacional
            
            excel_liq = io.BytesIO()
            wb_liq.save(excel_liq)
            zf.writestr(f"03_DADOS_LIQUIDAR_NF{nf_ebm}.xlsx", excel_liq.getvalue())
            
        st.success("Tudo pronto! Seus arquivos foram gerados com sucesso.")
        st.download_button(label="📥 Baixar Faturamento (ZIP)", data=zip_buffer.getvalue(), file_name=f"Faturamento_NF{nf_ebm}.zip", mime="application/zip")

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar a planilha. Verifique os dados fornecidos e se as planilhas modelos estão corretas.")

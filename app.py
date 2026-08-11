import streamlit as st
import io
import zipfile
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

st.set_page_config(page_title="Gerador de Faturamento EBM", layout="centered")

st.title("📊 Gerador de Faturamento - EBM Quintto")
st.write("Preencha as informações abaixo para gerar os 3 relatórios em PDF automaticamente.")

with st.form("faturamento_form"):
    col1, col2 = st.columns(2)
    tipo_servico = col1.selectbox("Tipo de Serviço", ["Mídia", "Produção", "Custos Internos"])
    empenho = col2.text_input("Nº do Empenho")
    
    nup = st.text_input("NUP (Ex: 30001.008502/2026-87)")
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
    valor_bruto = col9.number_input("Valor Bruto Total da NF (R$)", min_value=0.0, step=0.01)
    valor_fornecedor = col10.number_input("Valor Repassado ao Fornecedor (R$)", min_value=0.0, step=0.01)
    
    submit = st.form_submit_button("Gerar 3 PDFs")

if submit:
    try:
        # --- LÓGICA DE CÁLCULO DE IMPOSTOS ---
        honorarios_ebm = valor_bruto - valor_fornecedor
        
        # Impostos Fornecedor
        if simples_nacional == "SIM":
            ret_iss_forn = 0.0
            ret_irrf_forn = 0.0
        else:
            ret_iss_forn = valor_fornecedor * 0.02
            ret_irrf_forn = valor_fornecedor * 0.048
            
        ret_imp_forn = ret_iss_forn + ret_irrf_forn
        valor_liq_forn = valor_fornecedor - ret_imp_forn
        
        # Impostos EBM
        ret_iss_ebm = honorarios_ebm * 0.05
        ret_irrf_ebm = honorarios_ebm * 0.048
        ret_imp_ebm = ret_iss_ebm + ret_irrf_ebm
        valor_liq_ebm = honorarios_ebm - ret_imp_ebm
        
        valor_liq_total = valor_liq_forn + valor_liq_ebm
        total_iss = ret_iss_ebm + ret_iss_forn
        total_irrf = ret_irrf_ebm + ret_irrf_forn

        # Estilos do ReportLab
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        normal.fontSize = 10
        normal.leading = 14

        bold_style = ParagraphStyle('BoldStyle', parent=normal, fontName='Helvetica-Bold')
        title_style = ParagraphStyle('TitleStyle', parent=normal, fontName='Helvetica-Bold', fontSize=12, alignment=1)

        # --- GERADOR PDF 1: CARTA ---
        def gerart_carta_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
            story = []

            # Cabeçalho
            story.append(Paragraph(f"Fortaleza, {data_ebm}.", normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>À Casa Civil</b><br/>Att. Dra. Joelise Collyer Teixeira de Paula<br/>Secretária Executiva de Comunicação, Publicidade e Eventos.", normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"<b>Ref. Empenho nº {empenho}</b>", bold_style))
            story.append(Spacer(1, 15))
            story.append(Paragraph("Prezada Secretária,", normal))
            story.append(Spacer(1, 10))

            # Texto condicional por tipo
            if tipo_servico == "Custos Internos":
                texto = f"Segue para pagamento o processo de Custo Interno - EBMQUINTTO.<br/>PAGTO REF. A SERVIÇOS INTERNOS - {descricao} - EBM QUINTTO.<br/>CNPJ: 14.470.051/0001-91<br/>Nº {numero_doc} no valor de <b>R$ {valor_bruto:,.2f}</b>."
            elif tipo_servico == "Mídia":
                texto = f"Segue para pagamento o processo do Serviço de Mídia.<br/>PAGTO REF. {descricao}.<br/>CNPJ Veículo: {cnpj_forn} ({fornecedor})<br/>Documento Nº {numero_doc} no valor de <b>R$ {valor_bruto:,.2f}</b>."
            else: # Produção
                texto = f"Segue para pagamento o processo de Produção.<br/>PAGTO REF. A {descricao}.<br/>CNPJ Fornecedor: {cnpj_forn} ({fornecedor})<br/>Documento Nº {numero_doc} no valor de <b>R$ {valor_bruto:,.2f}</b>."

            story.append(Paragraph(texto, normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph("Através do contrato nº 177/2024.<br/>Na certeza de contarmos com o parecer favorável.<br/>Subscrevemo-nos,", normal))
            story.append(Spacer(1, 20))

            # Assinatura e Logo
            try:
                story.append(Image("assinatura da gabriela martins.jpeg", width=4*cm, height=2*cm))
            except:
                pass
            story.append(Paragraph("<b>EBM QUINTTO COMUNICAÇÃO LTDA</b><br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br", normal))
            
            doc.build(story)
            return buffer.getvalue()

        # --- GERADOR PDF 2: PLANILHA FINANCEIRA ---
        def gerar_financeira_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []

            story.append(Paragraph("<b>EBM QUINTTO - CONTROLE DE REPASSE (CASA CIVIL)</b>", title_style))
            story.append(Paragraph(f"CONTRATO 177/2024 | Nº EMPENHO: {empenho} | NF EBM: {nf_ebm} | EMISSÃO: {data_ebm}", normal))
            story.append(Spacer(1, 15))

            data_table = [
                ["Nº EMPENHO", "NF EBM", "FORNECEDOR", "NF FORN.", "VALOR FORN.", "RET. IMP.", "VALOR LÍQ. FORN.", "HONORÁRIOS EBM", "RET. IMP.", "VALOR LÍQ. EBM", "VALOR LÍQ. NF"],
                [empenho, nf_ebm, fornecedor, nf_forn, f"R$ {valor_fornecedor:,.2f}", f"R$ {ret_imp_forn:,.2f}", f"R$ {valor_liq_forn:,.2f}", f"R$ {honorarios_ebm:,.2f}", f"R$ {ret_imp_ebm:,.2f}", f"R$ {valor_liq_ebm:,.2f}", f"R$ {valor_liq_total:,.2f}"]
            ]

            t = Table(data_table, colWidths=[1.5*cm, 1.2*cm, 2.5*cm, 1.2*cm, 1.8*cm, 1.5*cm, 1.8*cm, 1.8*cm, 1.5*cm, 1.8*cm, 1.8*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ]))
            story.append(t)
            story.append(Spacer(1, 30))

            try:
                story.append(Image("assinatura da gabriela martins.jpeg", width=4*cm, height=2*cm))
            except:
                pass
            story.append(Paragraph("<b>Gabriela Martins</b> - Gerente Financeira", normal))

            doc.build(story)
            return buffer.getvalue()

        # --- GERADOR PDF 3: DADOS PARA LIQUIDAR ---
        def gerar_liquidar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []

            story.append(Paragraph("<b>DADOS PARA LIQUIDAÇÃO DE PROCESSO</b>", title_style))
            story.append(Spacer(1, 10))

            # Tabela Resumo Topo
            resumo_data = [
                ["EMPENHO", empenho, "NUP", nup],
                ["VALOR TOTAL", f"R$ {valor_bruto:,.2f}", "VALOR LÍQUIDO", f"R$ {valor_liq_total:,.2f}"],
                ["RETENÇÃO ISS", f"R$ {total_iss:,.2f}", "RETENÇÃO IRRF", f"R$ {total_irrf:,.2f}"]
            ]
            t_resumo = Table(resumo_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
            t_resumo.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(t_resumo)
            story.append(Spacer(1, 15))

            # Detalhamento
            detalhe_data = [
                ["AGÊNCIA / FORNECEDOR", "NF", "EMISSÃO", "CNPJ", "BASE CALC.", "ISS", "IRRF", "SIMPLES"],
                ["EBM QUINTTO", nf_ebm, data_ebm, "14.470.051/0001-91", f"R$ {honorarios_ebm:,.2f}", f"R$ {ret_iss_ebm:,.2f}", f"R$ {ret_irrf_ebm:,.2f}", "NÃO"],
                [fornecedor, nf_forn, data_forn, cnpj_forn, f"R$ {valor_fornecedor:,.2f}", f"R$ {ret_iss_forn:,.2f}", f"R$ {ret_irrf_forn:,.2f}", simples_nacional]
            ]
            t_detalhe = Table(detalhe_data, colWidths=[4*cm, 1.2*cm, 1.8*cm, 3*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm])
            t_detalhe.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D9D9D9')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('FONTSIZE', (0,0), (-1,-1), 7),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ]))
            story.append(t_detalhe)

            doc.build(story)
            return buffer.getvalue()

        # Criando o arquivo ZIP com os 3 PDFs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"01_CARTA_NF{nf_ebm}.pdf", gerart_carta_pdf())
            zf.writestr(f"02_PLANILHA_FINANCEIRA_NF{nf_ebm}.pdf", gerar_financeira_pdf())
            zf.writestr(f"03_DADOS_LIQUIDAR_NF{nf_ebm}.pdf", gerar_liquidar_pdf())

        st.success("Tudo pronto! Os 3 relatórios em PDF foram gerados com sucesso.")
        st.download_button(
            label="📥 Baixar 3 PDFs (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"Faturamento_PDFs_NF{nf_ebm}.zip",
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar os relatórios em PDF: {e}")

import streamlit as st
import io
import zipfile

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

st.set_page_config(page_title="Gerador de Faturamento EBM", layout="centered")

st.title("📊 Gerador de Faturamento - EBM Quintto")
st.write("Preencha as informações abaixo para gerar a Carta (Retrato) e os Controles (Paisagem).")

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
        # --- CÁLCULOS FINANCEIROS ---
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

        # --- ESTILOS BASE ---
        styles = getSampleStyleSheet()
        normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
        bold = ParagraphStyle('BoldCustom', parent=normal, fontName='Helvetica-Bold')
        title = ParagraphStyle('TitleCustom', parent=normal, fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=1)
        
        cell_header = ParagraphStyle('HeaderCell', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1, textColor=colors.whitesmoke)
        cell_body = ParagraphStyle('BodyCell', fontName='Helvetica', fontSize=8, leading=10, alignment=1)
        cell_body_bold = ParagraphStyle('BodyCellBold', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1)

        def p_head(txt): return Paragraph(txt, cell_header)
        def p_cell(txt, is_bold=False): return Paragraph(str(txt), cell_body_bold if is_bold else cell_body)

        # ==========================================
        # 1. GERADOR PDF 01_CARTA (RETRATO)
        # ==========================================
        def gerar_carta_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
            story = []

            story.append(Paragraph(f"Fortaleza, {data_ebm}.", normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>À<br/>Casa Civil</b><br/>Att. Dra. Joelise Collyer Teixeira de Paula<br/>Secretária Executiva de Comunicação, Publicidade e Eventos.", normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"<b>Ref. Empenho nº {empenho}</b>", bold))
            story.append(Spacer(1, 15))
            story.append(Paragraph("Prezada Secretária,", normal))
            story.append(Spacer(1, 10))

            if tipo_servico == "Custos Internos":
                texto = f"Segue para pagamento o processo de Custo Interno - EBMQUINTTO.<br/><br/>PAGTO REF. A SERVIÇOS INTERNOS - {descricao} - EBM QUINTTO<br/>CNPJ: 14.470.051/0001-91<br/>OC Nº {numero_doc} no valor de <b>R$ {valor_bruto:,.2f}</b>."
            elif tipo_servico == "Mídia":
                texto = f"Segue para pagamento o processo do Serviço de Mídia.<br/><br/>PAGTO REF. {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R$ {valor_bruto:,.2f}</b>."
            else:
                texto = f"Segue para pagamento o processo de Produção.<br/><br/>PAGTO REF. A {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R$ {valor_bruto:,.2f}</b>."

            story.append(Paragraph(texto, normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph("Através do contrato nº 177/2024.<br/>Na certeza de contarmos com o parecer favorável.<br/>Subscrevemo-nos,", normal))
            story.append(Spacer(1, 25))

            try:
                story.append(Image("assinatura da gabriela martins.jpeg", width=4*cm, height=1.8*cm))
            except:
                pass
            story.append(Paragraph("<b>EBM QUINTTO COMUNICAÇÃO LTDA</b><br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br", normal))
            
            doc.build(story)
            return buffer.getvalue()

        # ==========================================
        # 2. GERADOR PDF 02_PLANILHA FINANCEIRA (PAISAGEM)
        # ==========================================
        def gerar_financeira_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []

            story.append(Paragraph("<b>EBM QUINTTO COMUNICAÇÃO LTDA - CONTROLE DE REPASSE (CASA CIVIL)</b>", title))
            story.append(Spacer(1, 10))

            info_text = f"""
            <b>CONTRATO 177/2024</b> &nbsp;&nbsp;|&nbsp;&nbsp; <b>Nº EMPENHO:</b> {empenho} &nbsp;&nbsp;|&nbsp;&nbsp; <b>NF EBM:</b> {nf_ebm} &nbsp;&nbsp;|&nbsp;&nbsp; <b>EMISSÃO:</b> {data_ebm}<br/>
            <b>DOCUMENTO / REF:</b> {numero_doc} - PAGTO REF. {descricao} - {fornecedor if tipo_servico != 'Custos Internos' else 'EBM QUINTTO'}
            """
            story.append(Paragraph(info_text, normal))
            story.append(Spacer(1, 15))

            headers = [
                p_head("Nº EMP."), p_head("NF EBM"), p_head("FORNECEDOR / VEÍCULO"), p_head("NF FORN."), 
                p_head("VALOR FORN."), p_head("RET. IMP."), p_head("VALOR LÍQ. FORN."), 
                p_head("HONORÁRIOS EBM"), p_head("RET. IMP."), p_head("VALOR LÍQ. EBM"), p_head("VALOR LÍQ. NF")
            ]

            row = [
                p_cell(empenho), p_cell(nf_ebm), p_cell(fornecedor if tipo_servico != 'Custos Internos' else 'SERVIÇOS INTERNOS EBM'),
                p_cell(nf_forn if nf_forn else '-'), p_cell(f"R$ {valor_fornecedor:,.2f}"), p_cell(f"R$ {ret_imp_forn:,.2f}"),
                p_cell(f"R$ {valor_liq_forn:,.2f}"), p_cell(f"R$ {honorarios_ebm:,.2f}"), p_cell(f"R$ {ret_imp_ebm:,.2f}"),
                p_cell(f"R$ {valor_liq_ebm:,.2f}"), p_cell(f"R$ {valor_liq_total:,.2f}", is_bold=True)
            ]

            # Largura expandida para preencher os ~25 cm úteis do modo Paisagem
            col_widths = [2.0*cm, 1.8*cm, 4.2*cm, 1.8*cm, 2.3*cm, 2.0*cm, 2.3*cm, 2.3*cm, 2.0*cm, 2.3*cm, 2.5*cm]
            t = Table([headers, row], colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))

            story.append(Paragraph(f"<b>VALOR BRUTO TOTAL DA NF:</b> R$ {valor_bruto:,.2f}", bold))
            story.append(Paragraph(f"<b>VALOR LÍQUIDO A RECEBER:</b> R$ {valor_liq_total:,.2f}", bold))
            story.append(Spacer(1, 20))

            try:
                story.append(Image("assinatura da gabriela martins.jpeg", width=4*cm, height=1.8*cm))
            except:
                pass
            story.append(Paragraph("<b>Gabriela Martins</b><br/>Gerente Financeira - EBM QUINTTO", normal))

            doc.build(story)
            return buffer.getvalue()

        # ==========================================
        # 3. GERADOR PDF 03_DADOS PARA LIQUIDAR (PAISAGEM)
        # ==========================================
        def gerar_liquidar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []

            story.append(Paragraph("<b>DADOS PARA LIQUIDAÇÃO DE PROCESSO</b>", title))
            story.append(Spacer(1, 15))

            p_res_head = lambda txt: Paragraph(f"<b>{txt}</b>", ParagraphStyle('RHead', parent=normal, fontSize=9, fontName='Helvetica-Bold'))
            p_res_val = lambda txt: Paragraph(str(txt), ParagraphStyle('RVal', parent=normal, fontSize=9))

            resumo_data = [
                [p_res_head("EMPENHO"), p_res_val(empenho), p_res_head("NUP"), p_res_val(nup)],
                [p_res_head("VALOR TOTAL"), p_res_val(f"R$ {valor_bruto:,.2f}"), p_res_head("VALOR LÍQUIDO"), p_res_val(f"R$ {valor_liq_total:,.2f}")],
                [p_res_head("RETENÇÃO ISS"), p_res_val(f"R$ {total_iss:,.2f}"), p_res_head("RETENÇÃO IRRF"), p_res_val(f"R$ {total_irrf:,.2f}")]
            ]
            
            t_resumo = Table(resumo_data, colWidths=[4.5*cm, 8.0*cm, 4.5*cm, 8.5*cm])
            t_resumo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F2F2F2')),
                ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F2F2F2')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#B0C4DE')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_resumo)
            story.append(Spacer(1, 20))

            detalhe_headers = [
                p_head("RAZÃO SOCIAL / AGÊNCIA"), p_head("NF"), p_head("EMISSÃO"), p_head("CNPJ"), 
                p_head("BASE CÁLCULO"), p_head("ISS"), p_head("IRRF"), p_head("SIMPLES NACIONAL")
            ]

            row_ebm = [
                p_cell("EBM QUINTTO COMUNICAÇÃO LTDA", is_bold=True), p_cell(nf_ebm), p_cell(data_ebm), p_cell("14.470.051/0001-91"),
                p_cell(f"R$ {honorarios_ebm:,.2f}"), p_cell(f"R$ {ret_iss_ebm:,.2f}"), p_cell(f"R$ {ret_irrf_ebm:,.2f}"), p_cell("NÃO")
            ]

            row_forn = [
                p_cell(fornecedor if fornecedor else 'SEM FORNECEDOR TERCEIRO', is_bold=True), p_cell(nf_forn if nf_forn else '-'), 
                p_cell(data_forn if data_forn else '-'), p_cell(cnpj_forn if cnpj_forn else '-'),
                p_cell(f"R$ {valor_fornecedor:,.2f}"), p_cell(f"R$ {ret_iss_forn:,.2f}"), p_cell(f"R$ {ret_irrf_forn:,.2f}"), p_cell(simples_nacional)
            ]

            col_widths_det = [6.0*cm, 1.8*cm, 2.5*cm, 3.8*cm, 3.2*cm, 2.7*cm, 2.7*cm, 2.8*cm]
            t_detalhe = Table([detalhe_headers, row_ebm, row_forn], colWidths=col_widths_det)
            t_detalhe.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_detalhe)

            doc.build(story)
            return buffer.getvalue()

        # --- COMPACTAÇÃO EM ZIP ---
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"01_CARTA_NF{nf_ebm}.pdf", gerar_carta_pdf())
            zf.writestr(f"02_PLANILHA_FINANCEIRA_NF{nf_ebm}.pdf", gerar_financeira_pdf())
            zf.writestr(f"03_DADOS_LIQUIDAR_NF{nf_ebm}.pdf", gerar_liquidar_pdf())

        st.success("Tudo pronto! A Carta está em Retrato e os 2 Controles em Paisagem.")
        st.download_button(
            label="📥 Baixar 3 PDFs (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"Faturamento_PDFs_NF{nf_ebm}.zip",
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar os relatórios em PDF: {e}")

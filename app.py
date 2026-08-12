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
st.write("Preencha as informações abaixo para gerar os 3 relatórios em PDF.")

# Nome oficial da nova logo enviada
NOME_LOGO = "logo ebmquintto preta BG transparente.png"

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

# Helper para formatação de moeda brasileira (Ex: 1.440,00)
def fmt(val):
    return f"{val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

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

        # Estilos globais
        styles = getSampleStyleSheet()
        normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
        bold = ParagraphStyle('BoldCustom', parent=normal, fontName='Helvetica-Bold')
        title_center = ParagraphStyle('TitleCenter', parent=normal, fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1)

        # Células de tabela ajustadas
        cell_head = ParagraphStyle('CHead', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1)
        cell_body = ParagraphStyle('CBody', fontName='Helvetica', fontSize=6.5, leading=8, alignment=1)
        cell_body_bold = ParagraphStyle('CBodyBold', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1)

        def p_h(txt): return Paragraph(f"<b>{txt}</b>", cell_head)
        def p_c(txt, b=False): return Paragraph(str(txt), cell_body_bold if b else cell_body)

        # ==========================================
        # 1. GERADOR PDF 01_CARTA (RETRATO)
        # ==========================================
        def gerar_carta_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
            story = []

            try:
                story.append(Image(NOME_LOGO, width=3.8*cm, height=1.1*cm))
                story.append(Spacer(1, 15))
            except:
                pass

            story.append(Paragraph(f"Fortaleza, {data_ebm}.", normal))
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>À<br/>Casa Civil</b><br/>Att. Dra. Joelise Collyer Teixeira de Paula<br/>Secretária Executiva de Comunicação, Publicidade e Eventos.", normal))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Ref. Empenho nº {empenho}</b>", bold))
            story.append(Spacer(1, 12))
            story.append(Paragraph("Prezada Secretária,", normal))
            story.append(Spacer(1, 10))

            if tipo_servico == "Custos Internos":
                texto = f"Segue para pagamento o processo de Custo Interno - EBMQUINTTO.<br/><br/>PAGTO REF. A SERVIÇOS INTERNOS - {descricao} - EBM QUINTTO<br/>CNPJ: 14.470.051/0001-91<br/>OC Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."
            elif tipo_servico == "Mídia":
                texto = f"Segue para pagamento o processo do Serviço de Mídia.<br/><br/>PAGTO REF. {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."
            else:
                texto = f"Segue para pagamento o processo de Produção.<br/><br/>PAGTO REF. A {descricao}<br/>CNPJ: {cnpj_forn}<br/>Documento Nº {numero_doc} no valor de <b>R$ {fmt(valor_bruto)}</b>."

            story.append(Paragraph(texto, normal))
            story.append(Spacer(1, 15))
            story.append(Paragraph("Através do contrato nº 177/2024.<br/>Na certeza de contarmos com o parecer favorável.<br/>Subscrevemo-nos,", normal))
            story.append(Spacer(1, 20))

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
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
            story = []

            # Cabeçalho com Logo Nova e Título Centralizado
            p_header_text = Paragraph(f"""
            <b>CONTRATO 177/2024</b><br/>
            <b>CONTROLE DE REPASSE - CASA CIVIL</b><br/>
            <b>Nº EMPENHO {empenho}</b><br/>
            <b>NF EBM QUINTTO Nº {nf_ebm}</b><br/>
            <b>.:. EMISSÃO {data_ebm} .:. RECEBIMENTO // .:.</b>
            """, title_center)

            try:
                img_logo = Image(NOME_LOGO, width=3.8*cm, height=1.1*cm)
                h_table = Table([[img_logo, p_header_text]], colWidths=[4*cm, 21.5*cm])
                h_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,0), 'LEFT')]))
                story.append(h_table)
            except:
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
                p_c(f"R$ {fmt(valor_fornecedor)}", True), p_c(fmt(ret_imp_forn), True), p_c(fmt(valor_liq_forn), True),
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
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

            try:
                img_ass = Image("assinatura da gabriela martins.jpeg", width=3.5*cm, height=1.4*cm)
                p_ass_txt = Paragraph("<b>Gabriela S. Martins</b><br/><font size=5>EBM QUINTTO COMUNICAÇÃO LTDA<br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br</font>", cell_body)
                ass_box = Table([[img_ass], [p_ass_txt]], colWidths=[4.5*cm])
                ass_box.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                
                layout_ass = Table([['', ass_box]], colWidths=[21*cm, 4.5*cm])
                story.append(layout_ass)
            except:
                pass

            doc.build(story)
            return buffer.getvalue()

        # ==========================================
        # 3. GERADOR PDF 03_DADOS PARA LIQUIDAR (PAISAGEM)
        # ==========================================
        def gerar_liquidar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
            story = []

            p_lh = lambda txt: Paragraph(f"<b>{txt}</b>", ParagraphStyle('LH', parent=normal, fontSize=7, fontName='Helvetica-Bold'))
            p_lv = lambda txt: Paragraph(str(txt), ParagraphStyle('LV', parent=normal, fontSize=7, alignment=1))

            res_data = [
                [p_lh("EMPENHO"), p_lv(empenho)],
                [p_lh("NUP"), p_lv(nup)],
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
            
            layout_top = Table([[t_res, '']], colWidths=[8*cm, 17.5*cm])
            layout_top.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(layout_top)
            story.append(Spacer(1, 15))

            # Tabela 1: Agência
            head_ag = [p_h("NF AGÊNCIA"), p_h("DATA EMISSÃO"), p_h("CNPJ"), p_h("RAZÃO SOCIAL"), p_h("ISS"), p_h("IRRF"), p_h("BASE DE CÁLCULO"), p_h("SIMPLES NACIONAL")]
            row_ag = [p_c(nf_ebm), p_c(data_ebm), p_c("14470051000191"), p_c("EBM QUINTTO COMUNICAÇÃO LTDA"), p_c(fmt(ret_iss_ebm)), p_c(fmt(ret_irrf_ebm)), p_c(fmt(honorarios_ebm)), p_c("NÃO")]
            tot_ag = [p_c("TOTAL", True), p_c(''), p_c(''), p_c(''), p_c(fmt(ret_iss_ebm), True), p_c(fmt(ret_irrf_ebm), True), p_c(fmt(honorarios_ebm), True), p_c('')]

            col_w3 = [2.5*cm, 2.2*cm, 3.2*cm, 7.0*cm, 1.8*cm, 1.8*cm, 2.7*cm, 2.3*cm]
            t_ag = Table([head_ag, row_ag, tot_ag], colWidths=col_w3)
            t_ag.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D9D9D9')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(t_ag)
            story.append(Spacer(1, 12))

            # Tabela 2: Fornecedor
            head_fo = [p_h("NF FORNECEDOR"), p_h("DATA EMISSÃO"), p_h("CNPJ"), p_h("RAZÃO SOCIAL"), p_h("ISS"), p_h("IRRF"), p_h("BASE DE CÁLCULO"), p_h("SIMPLES NACIONAL")]
            row_fo = [p_c(nf_forn if nf_forn else ''), p_c(data_forn if data_forn else ''), p_c(cnpj_forn if cnpj_forn else ''), p_c(fornecedor if fornecedor else ''), p_c(fmt(ret_iss_forn)), p_c(fmt(ret_irrf_forn)), p_c(fmt(valor_fornecedor)), p_c(simples_nacional)]
            tot_fo = [p_c("TOTAL", True), p_c(''), p_c(''), p_c(''), p_c(fmt(ret_iss_forn), True), p_c(fmt(ret_irrf_forn), True), p_c(fmt(valor_fornecedor), True), p_c('')]

            t_fo = Table([head_fo, row_fo, tot_fo], colWidths=col_w3)
            t_fo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D9D9D9')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(t_fo)
            story.append(Spacer(1, 15))

            try:
                img_ass = Image("assinatura da gabriela martins.jpeg", width=3.5*cm, height=1.4*cm)
                p_ass_txt = Paragraph("<b>Gabriela S. Martins</b><br/><font size=5>EBM QUINTTO COMUNICAÇÃO LTDA<br/>Gabriela Martins - Gerente Financeira<br/>gabriela.martins@ebmquintto.com.br</font>", cell_body)
                ass_box = Table([[img_ass], [p_ass_txt]], colWidths=[4.5*cm])
                ass_box.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT')]))
                
                layout_ass = Table([[ass_box, '']], colWidths=[4.5*cm, 21*cm])
                story.append(layout_ass)
            except:
                pass

            doc.build(story)
            return buffer.getvalue()

        # --- COMPACTAÇÃO EM ZIP ---
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"01_CARTA_NF{nf_ebm}.pdf", gerar_carta_pdf())
            zf.writestr(f"02_PLANILHA_FINANCEIRA_NF{nf_ebm}.pdf", gerar_financeira_pdf())
            zf.writestr(f"03_DADOS_LIQUIDAR_NF{nf_ebm}.pdf", gerar_liquidar_pdf())

        st.success("Tudo pronto! Relatórios gerados com a nova logo HD com fundo transparente.")
        st.download_button(
            label="📥 Baixar 3 PDFs (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"Faturamento_PDFs_NF{nf_ebm}.zip",
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar os relatórios em PDF: {e}")

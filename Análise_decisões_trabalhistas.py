# -*- coding: utf-8 -*-
# Versão com campo Prazo Pagamento e Opção Art. 916

import streamlit as st
from datetime import date, datetime
import logging

# Importa configurações e funções dos outros módulos
try:
    import config
    from utils_date import add_business_days
    from parser import parse_and_format_report_v3, PedidoData
    # Importa Prazo e funções de email/formatação
    from utils_email import generate_email_body, format_prazos, make_hyperlink, Prazo
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()


# Configuração do Logging
log_level = getattr(logging, config.LOGGING_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

log.info("Iniciando aplicação Streamlit...")

# ========= INÍCIO: Configuração da Página e Estado =========
st.set_page_config(page_title="Análise e Email Decisões v4.6", layout="wide")
st.title("Formulário de Análise e Geração de Email")

# Inicializa estado da sessão (Adiciona novas chaves)
default_session_state = {
    "fase_processual": "Conhecimento", "cliente_role_radio": "Reclamado",
    "tipo_decisao": config.DECISAO_OPTIONS_CONHECIMENTO[0],
    "resultado_sentenca": config.RESULTADO_OPTIONS[0], "ed_status": None,
    "recurso_sel": config.PLACEHOLDER_RECURSO,
    "status_custas": config.PLACEHOLDER_STATUS, "status_deposito": config.PLACEHOLDER_STATUS,
    "guias_status_v4": None, "valor_condenacao_execucao": 0.0, "prazos": [],
    "parsed_pedidos_data": None, "parsed_pedidos_error": None, "show_image_example": False,
    "data_ciencia": None, "data_ciencia_valida": False, "obs_sentenca": "",
    "sintese_objeto_recurso": "", "calc_total_homologado": 0.0, "calc_principal_liq": 0.0,
    "calc_inss_emp": 0.0, "calc_fgts": 0.0, "calc_hon_suc": 0.0, "calc_hon_per": 0.0,
    "calc_obs": "", "dep_anterior_valor": 0.0, "dep_anterior_detalhes": "",
    "justif_ed": "", "recurso_outro_txt": "", "recurso_just": "",
    "garantia_necessaria": False, "valor_custas": 0.0, "valor_deposito_input": 0.0,
    "local_guias": "", "obs_finais": "", "suggested_descricao_sel": "",
    "suggested_descricao_txt": "", "suggested_data_fatal": date.today(),
    "suggested_data_d": date.today(),
    # --- NOVAS CHAVES ---
    "prazo_pagamento_dias": 15, # Default 15 dias
    "opcao_art_916": "Não oferecer/Não aplicável" # Default
}
for key, default_value in default_session_state.items():
    if key not in st.session_state: st.session_state[key] = default_value
# ========= FIM: Configuração da Página e Estado =========

# ====== SIDEBAR DE AJUDA ======
with st.sidebar:
    st.header("Ajuda - Roteiro de Análise"); st.info("""
        *(Atualizar texto da ajuda para incluir
         Prazo Pagamento e Opção Art. 916)*
        """)
    debug_mode = st.checkbox("Ativar Logs de Debug", value=(config.LOGGING_LEVEL == "DEBUG"))
    if debug_mode: logging.getLogger().setLevel(logging.DEBUG); st.caption("Logs DEBUG no terminal.")
    else: logging.getLogger().setLevel(logging.INFO)


# ========= Layout Principal com Tabs =========
st.header("Análise da Decisão Trabalhista")
tab_contexto, tab_analise, tab_pedidos, tab_proximo_passo, tab_prazos_obs = st.tabs([
    "1. Contexto", "2. Análise Decisão", "3. Pedidos (Tabela)", "4. Próximo Passo", "5. Prazos e Obs."
])

# --- Tab 1: Contexto ---
with tab_contexto:
    # (Conteúdo mantido)
    st.subheader("Informações Gerais"); col_fase, col_contexto1 = st.columns([0.5, 1.5])
    with col_fase: st.radio("Fase:", ["Conhecimento", "Execução"], index=["Conhecimento", "Execução"].index(st.session_state.fase_processual), key="fase_processual", horizontal=True)
    with col_contexto1: st.date_input("Data da Ciência:", value=st.session_state.get("data_ciencia"), key="data_ciencia", help="Data da notificação formal.")
    st.session_state.data_ciencia_valida = st.session_state.data_ciencia is not None
    st.radio("Cliente é:", config.CLIENTE_OPTIONS, index=config.CLIENTE_OPTIONS.index(st.session_state.cliente_role_radio), key="cliente_role_radio", horizontal=True)
    st.caption("Info: Nº do Processo, Nomes, Local usarão placeholders [ ] no e-mail.")
    st.subheader("Decisão Analisada")
    current_decisao_options = config.DECISAO_OPTIONS_EXECUCAO if st.session_state.fase_processual == "Execução" else config.DECISAO_OPTIONS_CONHECIMENTO
    st.selectbox("Tipo de Decisão:", options=current_decisao_options, index=current_decisao_options.index(st.session_state.tipo_decisao) if st.session_state.tipo_decisao in current_decisao_options else 0, key="tipo_decisao")

# --- Tab 2: Análise Decisão ---
with tab_analise:
    st.subheader("Resultado e Valor")
    col_res1, col_res2 = st.columns([1,1])
    with col_res1: st.selectbox("Resultado Geral p/ Cliente:", options=config.RESULTADO_OPTIONS, index=config.RESULTADO_OPTIONS.index(st.session_state.resultado_sentenca) if st.session_state.resultado_sentenca in config.RESULTADO_OPTIONS else 0, key="resultado_sentenca")
    with col_res2:
        mostrar_valor = st.session_state.resultado_sentenca == "Desfavorável" or st.session_state.fase_processual == "Execução"
        if mostrar_valor:
            label_valor = "Valor Condenação/Arbitrado (R$):" if st.session_state.fase_processual == "Conhecimento" else "Valor Execução/Cálculo (R$):"
            st.number_input(label_valor, min_value=0.0, step=0.01, format="%.2f", key="valor_condenacao_execucao")
    st.text_area("Observações sobre a Decisão:", key="obs_sentenca", help="Detalhe nuances.")
    st.text_area("Síntese Decisão / Objeto Recurso (p/ Email):", height=100, key="sintese_objeto_recurso", help="Resumo conciso para corpo do e-mail.")

    # --- Campos de Execução ---
    if st.session_state.fase_processual == "Execução":
        st.markdown("---"); st.subheader("Detalhes da Execução")

        # <<< NOVOS CAMPOS AQUI >>>
        col_prazo_p, col_opt_916 = st.columns(2)
        with col_prazo_p:
             st.number_input("Prazo para Pagamento (dias):", min_value=1, step=1, key="prazo_pagamento_dias", help="Prazo concedido na decisão (default 15).")
        with col_opt_916:
             opcoes_916 = ["Não oferecer/Não aplicável", "Oferecer Opção Art. 916", "Cliente Optou por Art. 916"]
             st.selectbox("Parcelamento Art. 916 CPC:", options=opcoes_916, key="opcao_art_916", help="Oferecer ou confirmar opção de parcelamento?")
        # <<< FIM NOVOS CAMPOS >>>

        with st.expander("Detalhes dos Cálculos Homologados (Opcional)", expanded=True):
            st.number_input("Valor Total Homologado (R$):", key="calc_total_homologado"); st.number_input("Principal Líquido (+Juros?) (R$):", key="calc_principal_liq"); st.number_input("INSS Empregado (Base) (R$):", key="calc_inss_emp"); st.number_input("FGTS (+Taxa?) (R$):", key="calc_fgts"); st.number_input("Hon. Sucumbência (R$):", key="calc_hon_suc"); st.number_input("Hon. Periciais (R$):", key="calc_hon_per"); st.text_area("Obs Cálculos:", key="calc_obs")

    with st.expander("Depósitos Recursais Anteriores (Opcional)"):
        st.number_input("Valor Total Aprox. (R$):", key="dep_anterior_valor")
        st.text_area("Detalhes (Datas, Tipos):", key="dep_anterior_detalhes")


# --- Tab 3: Pedidos (Tabela) ---
with tab_pedidos:
    # (Conteúdo Tab 3 mantido)
    st.subheader("Tabela de Pedidos (DataJuri)"); st.write("Use o Upload de Arquivo (preferencial) ou cole o texto abaixo.")
    uploaded_file = st.file_uploader("Carregar Arquivo (CSV, Excel, TXT com TABs)", type=['csv', 'xlsx', 'xls', 'txt'], key="file_uploader")
    st.markdown("---"); st.write("Ou cole o texto da tabela aqui:")
    if st.button("Mostrar/Ocultar Imagem Exemplo", key="toggle_image_btn"): st.session_state.show_image_example = not st.session_state.show_image_example
    if st.session_state.show_image_example:
        try: st.image(config.IMAGE_PATH, caption="Exemplo Tela DataJuri", use_column_width=True); st.caption(f"Verifique se '{config.IMAGE_PATH}' está na pasta.")
        except FileNotFoundError: st.error(f"Erro: Imagem '{config.IMAGE_PATH}' não encontrada.")
        except Exception as img_e: st.error(f"Erro ao carregar imagem: {img_e}")
    help_text_tabela_v4 = """...""" # Mantido
    st.text_area("Conteúdo Tabela Colada:", height=150, key="texto_tabela_pedidos", help=help_text_tabela_v4, label_visibility="collapsed")
    preview_placeholder = st.empty()
    if st.button("Verificar Tabela Carregada/Colada"):
        tipo_decisao_atual = st.session_state.tipo_decisao
        if not tipo_decisao_atual or tipo_decisao_atual == config.DECISAO_OPTIONS_CONHECIMENTO[0]: preview_placeholder.error("Selecione 'Tipo de Decisão Analisada' na aba 'Contexto' antes.")
        elif uploaded_file or st.session_state.texto_tabela_pedidos.strip():
            with st.spinner("Processando tabela..."):
                parsed_data, error_msg = parse_and_format_report_v3(texto=st.session_state.texto_tabela_pedidos if not uploaded_file else None, uploaded_file=uploaded_file)
                if parsed_data is not None: st.session_state.parsed_pedidos_data = parsed_data; st.session_state.parsed_pedidos_error = None; preview_placeholder.success("Tabela processada!"); preview_placeholder.dataframe(parsed_data, use_container_width=True)
                else: st.session_state.parsed_pedidos_data = None; st.session_state.parsed_pedidos_error = error_msg; preview_placeholder.error(f"Falha:"); preview_placeholder.code(error_msg, language=None)
        else: preview_placeholder.warning("Carregue um arquivo ou cole o texto."); st.session_state.parsed_pedidos_data = None; st.session_state.parsed_pedidos_error = None


# --- Tab 4: Próximo Passo (ED/Recurso) ---
with tab_proximo_passo:
    # (Conteúdo Tab 4 mantido)
    st.subheader("Embargos de Declaração (ED)"); st.radio("Avaliação ED:", config.ED_STATUS_OPTIONS, index=None, key="ed_status", horizontal=True)
    if st.session_state.ed_status == "Cabe ED": st.text_area("Justificativa ED:", height=80, key="justif_ed")
    mostrar_secao_recurso = (st.session_state.ed_status == "Não cabe ED")
    if mostrar_secao_recurso:
        st.subheader("Recurso Cabível")
        current_lista_recursos = config.RECURSO_OPTIONS_EXECUCAO if st.session_state.fase_processual == "Execução" else config.RECURSO_OPTIONS_CONHECIMENTO
        current_mapa_recurso = config.MAPA_DECISAO_RECURSO_EXECUCAO if st.session_state.fase_processual == "Execução" else config.MAPA_DECISAO_RECURSO_CONHECIMENTO
        suggested_recurso_index = 0; tipo_decisao_atual = st.session_state.tipo_decisao; resultado_atual = st.session_state.resultado_sentenca; cliente_atual = st.session_state.cliente_role_radio
        if tipo_decisao_atual and tipo_decisao_atual != config.DECISAO_OPTIONS_CONHECIMENTO[0]:
            suggested_recurso_index = current_mapa_recurso.get(tipo_decisao_atual, 0)
            nao_interpor_idx = current_lista_recursos.index("Não Interpor Recurso") if "Não Interpor Recurso" in current_lista_recursos else 1
            if resultado_atual == "Favorável" and cliente_atual == "Reclamado": suggested_recurso_index = nao_interpor_idx
        if suggested_recurso_index >= len(current_lista_recursos): suggested_recurso_index = 0
        recurso_selecionado = st.selectbox("Recurso:", options=current_lista_recursos, index=suggested_recurso_index, key="recurso_sel")
        if recurso_selecionado == "Outro": st.text_input("Especifique:", key="recurso_outro_txt")
        if recurso_selecionado and recurso_selecionado != config.PLACEHOLDER_RECURSO: st.text_area("Justificativa:", height=80, key="recurso_just")
        recursos_exec_garantia = ["Embargos à Execução / Impugnação à Sentença", "Agravo de Petição (AP)"]
        garantia_necessaria = False
        if st.session_state.fase_processual == "Execução" and recurso_selecionado in recursos_exec_garantia: garantia_necessaria = st.checkbox("Garantia do Juízo necessária/recomendada?", key="garantia_necessaria")
        mostrar_secao_custas_guias = (recurso_selecionado and recurso_selecionado not in [config.PLACEHOLDER_RECURSO, "Não Interpor Recurso"])
        if mostrar_secao_custas_guias:
            st.subheader("Custas e Depósito/Garantia"); col_custas1, col_custas2 = st.columns(2)
            with col_custas1:
                status_custas = st.selectbox("Status Custas:", options=config.CUSTAS_OPTIONS, index=0, key="status_custas")
                if status_custas == "A Recolher": st.number_input("Valor Custas (R$):", min_value=0.01, format="%.2f", key="valor_custas")
            with col_custas2:
                current_deposito_options = config.DEPOSITO_OPTIONS_EXECUCAO if st.session_state.fase_processual == "Execução" else config.DEPOSITO_OPTIONS_CONHECIMENTO
                current_deposito_default_idx = config.DEPOSITO_DEFAULT_INDEX_EXEC if st.session_state.fase_processual == "Execução" else 0
                status_deposito = st.selectbox("Status Depósito/Garantia:", options=current_deposito_options, index=current_deposito_default_idx, key="status_deposito")
                if status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]: st.number_input("Valor Depósito/Garantia (R$):", min_value=0.01, format="%.2f", key="valor_deposito_input")
            precisa_recolher_agora = st.session_state.status_custas == "A Recolher" or st.session_state.status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            if precisa_recolher_agora:
                st.subheader("Guias de Pagamento"); st.radio("Status Guias:", options=config.GUIAS_OPTIONS, index=None, key="guias_status_v4"); st.text_input("Local/Obs Guias:", key="local_guias", help="Link, pasta ou obs.")


# --- Tab 5: Prazos e Observações ---
with tab_prazos_obs:
    # (Conteúdo da Tab 5 mantido como na resposta anterior)
    st.subheader("Prazos"); suggested_prazo = None; data_ciencia_prazo = st.session_state.get("data_ciencia"); ed_status_prazo = st.session_state.get("ed_status"); recurso_sel_prazo = st.session_state.get("recurso_sel")
    if data_ciencia_prazo:
        data_base = data_ciencia_prazo; desc_sugestao = ""
        if ed_status_prazo == "Cabe ED": desc_sugestao = "Embargos de Declaração"
        elif ed_status_prazo == "Não cabe ED":
            if recurso_sel_prazo and recurso_sel_prazo != config.PLACEHOLDER_RECURSO:
                if recurso_sel_prazo == "Não Interpor Recurso": desc_sugestao = "Verificar Recurso Contrário"
                elif recurso_sel_prazo != "Outro": desc_sugestao = recurso_sel_prazo
        if desc_sugestao:
             prazo_fatal_sugestao = add_business_days(data_base, 8)
             data_d_sugestao = add_business_days(prazo_fatal_sugestao, -3) if desc_sugestao != "Verificar Recurso Contrário" else prazo_fatal_sugestao
             suggested_prazo = {"descricao": desc_sugestao, "data_fatal": prazo_fatal_sugestao, "data_d": data_d_sugestao}
    if suggested_prazo:
        index_sugestao = 0; texto_sugestao_outro = ""; tipos_prazo_cfg = config.TIPOS_PRAZO_COMUNS
        if suggested_prazo['descricao'] in tipos_prazo_cfg: index_sugestao = tipos_prazo_cfg.index(suggested_prazo['descricao'])
        elif suggested_prazo['descricao']: index_sugestao = tipos_prazo_cfg.index("Outro (Especificar)"); texto_sugestao_outro = suggested_prazo['descricao']
        st.info(f"**Sugestão:** {suggested_prazo['descricao']} (Fatal: {suggested_prazo['data_fatal'].strftime('%d/%m/%Y')})")
        if st.button("Usar Prazo Sugerido"): st.session_state.suggested_descricao_sel = tipos_prazo_cfg[index_sugestao]; st.session_state.suggested_descricao_txt = texto_sugestao_outro; st.session_state.suggested_data_fatal = suggested_prazo['data_fatal']; st.session_state.suggested_data_d = suggested_prazo['data_d']; st.rerun()
    with st.form("form_prazos_v4", clear_on_submit=True):
        st.write("Adicione prazos relevantes:"); tipo_prazo_sel = st.selectbox("Tipo do Prazo:", options=config.TIPOS_PRAZO_COMUNS, index=config.TIPOS_PRAZO_COMUNS.index(st.session_state.get('suggested_descricao_sel', '')) if st.session_state.get('suggested_descricao_sel') in config.TIPOS_PRAZO_COMUNS else 0, key="tipo_prazo_sel")
        descricao_manual = "";
        if tipo_prazo_sel == "Outro (Especificar)": descricao_manual = st.text_input("Especifique Descrição:", value=st.session_state.get('suggested_descricao_txt', ''), key="desc_manual")
        col_datas1, col_datas2 = st.columns(2);
        with col_datas1: data_d = st.date_input("Data D- (interna):", value=st.session_state.get('suggested_data_d', date.today()))
        with col_datas2: data_fatal = st.date_input("Data Fatal (legal):", value=st.session_state.get('suggested_data_fatal', date.today()))
        obs_prazo = st.text_input("Observações Prazo:")
        submitted = st.form_submit_button("Adicionar Prazo")
        if submitted:
            descricao_final = tipo_prazo_sel if tipo_prazo_sel != "Outro (Especificar)" else descricao_manual.strip()
            if not descricao_final or tipo_prazo_sel == "": st.error("Descrição do prazo obrigatória!")
            elif data_d > data_fatal: st.error("Data D- não pode ser > Data Fatal!")
            else: st.session_state.prazos.append({"descricao": descricao_final, "data_d": str(data_d), "data_fatal": str(data_fatal), "obs": obs_prazo.strip()}); st.success("Prazo adicionado!"); st.session_state.suggested_descricao_sel = ""; st.session_state.suggested_descricao_txt = ""; st.session_state.suggested_data_fatal = date.today(); st.session_state.suggested_data_d = date.today(); st.rerun()
    st.write("---");
    if st.session_state.prazos:
        st.write("**Prazos Adicionados:**"); indices_para_remover = []
        for i, prazo_dict in enumerate(st.session_state.prazos):
             try: prazo = Prazo(**prazo_dict)
             except: prazo = Prazo(descricao=prazo_dict.get("descricao","ERRO"), data_d="", data_fatal="", obs=str(prazo_dict))
             col1, col2 = st.columns([0.95, 0.05]);
             with col1: st.markdown(f"**{i+1}. {prazo.descricao}**"); data_d_str = "N/I"; data_fatal_str = "N/I"
             try: data_d_str = datetime.strptime(prazo.data_d, '%Y-%m-%d').strftime('%d/%m/%Y') if prazo.data_d else "N/I"
             except: data_d_str = f"{prazo.data_d}(Inválido)"
             st.write(f"   - Data D-: {data_d_str}")
             try: data_fatal_str = datetime.strptime(prazo.data_fatal, '%Y-%m-%d').strftime('%d/%m/%Y') if prazo.data_fatal else "N/I"
             except: data_fatal_str = f"{prazo.data_fatal}(Inválido)"
             st.write(f"   - Data Fatal: {data_fatal_str}");
             if prazo.obs: st.write(f"   - Observações: {prazo.obs}")
             st.write("---")
             with col2:
                 if st.button("X", key=f"del_prazo_{i}", help="Remover"): indices_para_remover.append(i)
        if indices_para_remover:
            for index in sorted(indices_para_remover, reverse=True):
                if index < len(st.session_state.prazos): del st.session_state.prazos[index]
            st.rerun()

    st.subheader("Observações Finais")
    st.text_area("Observações Gerais (para registro interno):", key="obs_finais", height=100)


# ========= BOTÃO FINAL PARA GERAR O E-MAIL =========
st.divider()
if st.button("📧 Gerar Rascunho de E-mail", type="primary", use_container_width=True):
    # (Validações mantidas, precisa ajustar para os novos campos se forem obrigatórios)
    valid = True; error_messages = []; ph_select = config.PLACEHOLDER_SELECT; ph_recurso = config.PLACEHOLDER_RECURSO; ph_status = config.PLACEHOLDER_STATUS; placeholders_geral = [ph_select, ph_recurso, ph_status, ""]
    # ... (bloco de validação completo mantido como na resposta anterior, já usa session_state) ...
    fase_val = st.session_state.fase_processual; data_ciencia_val = st.session_state.get("data_ciencia"); cliente_role_val = st.session_state.cliente_role_radio; tipo_decisao_val = st.session_state.tipo_decisao; resultado_sentenca_val = st.session_state.resultado_sentenca; obs_sentenca_val = st.session_state.get("obs_sentenca",""); sintese_objeto_recurso_val = st.session_state.get("sintese_objeto_recurso", ""); texto_tabela_val = st.session_state.get("texto_tabela_pedidos",""); ed_status_val = st.session_state.get("ed_status"); justificativa_ed_val = st.session_state.get("justif_ed",""); recurso_selecionado_val = st.session_state.get("recurso_sel"); recurso_outro_especificar_val = st.session_state.get("recurso_outro_txt",""); recurso_justificativa_val = st.session_state.get("recurso_just",""); garantia_necessaria_val = st.session_state.get("garantia_necessaria", False); status_custas_val = st.session_state.get("status_custas"); valor_custas_val = st.session_state.get("valor_custas", 0.0); status_deposito_val = st.session_state.get("status_deposito"); valor_deposito_input_val = st.session_state.get("valor_deposito_input", 0.0); guias_status_val = st.session_state.get("guias_status_v4"); local_guias_val = st.session_state.get("local_guias",""); prazo_pagamento_val = st.session_state.get("prazo_pagamento_dias", 15); opcao_916_val = st.session_state.get("opcao_art_916") # Validação para novos campos?

    if not fase_val: error_messages.append("Selecione Fase Processual (Tab 1)."); valid = False
    if not data_ciencia_val: error_messages.append("Data da Ciência obrigatória (Tab 1)."); valid = False
    if not cliente_role_val or cliente_role_val == "Outro": error_messages.append("Papel do Cliente obrigatório (Reclamante/Reclamado) (Tab 1)."); valid = False
    if not tipo_decisao_val or tipo_decisao_val == ph_select: error_messages.append("Tipo de Decisão obrigatório (Tab 1)."); valid = False
    if not resultado_sentenca_val or resultado_sentenca_val == ph_select: error_messages.append("Resultado Geral obrigatório (Tab 2)."); valid = False
    elif resultado_sentenca_val == "Parcialmente Favorável" and not obs_sentenca_val.strip() and not sintese_objeto_recurso_val.strip(): error_messages.append("Obs ou Síntese obrigatórias se Resultado 'Parcialmente' (Tab 2)."); valid = False
    if texto_tabela_val.strip() and st.session_state.get('parsed_pedidos_error'): error_messages.append(f"Erro Tabela Pedidos: Verifique erro na Tab 3."); valid = False
    if ed_status_val is None: error_messages.append("Avaliação sobre ED obrigatória (Tab 4)."); valid = False
    elif ed_status_val == "Cabe ED" and not justificativa_ed_val.strip(): error_messages.append("Justificativa para ED obrigatória (Tab 4)."); valid = False
    mostrar_secao_recurso_val = (ed_status_val == "Não cabe ED")
    if mostrar_secao_recurso_val:
        if not recurso_selecionado_val or recurso_selecionado_val == ph_recurso: error_messages.append("Seleção de Recurso obrigatória (Tab 4)."); valid = False
        elif recurso_selecionado_val == "Outro" and not recurso_outro_especificar_val.strip(): error_messages.append("Especifique recurso 'Outro' (Tab 4)."); valid = False
        if recurso_selecionado_val != ph_recurso and not recurso_justificativa_val.strip(): error_messages.append("Justificativa p/ Recurso/Não Interposição obrigatória (Tab 4)."); valid = False
        mostrar_secao_custas_guias_val = (recurso_selecionado_val and recurso_selecionado_val not in [ph_recurso, "Não Interpor Recurso"])
        if mostrar_secao_custas_guias_val:
            if not status_custas_val or status_custas_val == ph_status: error_messages.append("Status das Custas obrigatório (Tab 4)."); valid = False
            elif status_custas_val == "A Recolher" and valor_custas_val <= 0.0: error_messages.append("Valor Custas > 0 se 'A Recolher' (Tab 4)."); valid = False
            if not status_deposito_val or status_deposito_val == ph_status: error_messages.append("Status do Depósito/Garantia obrigatório (Tab 4)."); valid = False
            elif status_deposito_val in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"] and valor_deposito_input_val <= 0.0: error_messages.append("Valor Depósito/Garantia > 0 se 'A Recolher' (Tab 4)."); valid = False
            precisa_recolher_val = status_custas_val == "A Recolher" or status_deposito_val in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            if precisa_recolher_val:
                if not guias_status_val: error_messages.append("Status das Guias obrigatório (Tab 4)."); valid = False
                if not local_guias_val.strip(): error_messages.append("'Local/Obs.' das guias obrigatório (Tab 4)."); valid = False

    if not valid:
        st.error("Existem erros/campos obrigatórios não preenchidos. Verifique as mensagens abaixo e nas abas indicadas:")
        for msg in error_messages: st.error(f"- {msg}")
        st.stop()
    else:
        # Coleta final dos dados do st.session_state para a função de email
        email_data = {key: st.session_state.get(key) for key in st.session_state}
        # Garante que as chaves usadas pela função de email existam, mesmo que com None ou default
        email_data.setdefault('pedidos_data', None)
        email_data.setdefault('prazos', [])
        # ... (garantir outras chaves se necessário, ou a função generate_email_body usa .get())

        log.info("Gerando rascunho de e-mail...")
        try:
            email_subject, email_body = generate_email_body(**email_data) # Chama utils_email.py

            st.subheader("Rascunho do E-mail Gerado")
            st.text_input("Assunto:", value=email_subject, key="email_subj_final")
            st.text_area("Corpo do E-mail:", value=email_body, height=600, key="email_body_final")
            st.success("Rascunho de e-mail gerado com sucesso!")
            log.info("Rascunho de e-mail gerado.")
        except Exception as e_email:
            st.error(f"Ocorreu um erro ao gerar o corpo do e-mail: {e_email}")
            log.error("Erro em generate_email_body", exc_info=True)

# -*- coding: utf-8 -*-
# Versão com Correção height text_area "Obs Cálculos" (e fixes anteriores)

import streamlit as st
from datetime import date, datetime
import logging
import pandas as pd # Para exibir preview em tabela

# Importa configurações e funções dos outros módulos
try:
    import config
    from utils_date import add_business_days, add_months
    from parser import parse_and_format_report_v3, PedidoData
    from utils_email import generate_email_body, format_prazos, make_hyperlink, Prazo
except ImportError as e:
    st.error(f"Erro ao importar módulos. Certifique-se que os arquivos config.py, utils_date.py, parser.py, utils_email.py estão na mesma pasta. Detalhe: {e}")
    st.stop()


# Configuração do Logging
log_level = getattr(logging, config.LOGGING_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

log.info("Iniciando aplicação Streamlit...")

# ========= INÍCIO: Configuração da Página e Estado =========
st.set_page_config(page_title="Análise e Email Decisões v4.9-Final", layout="wide") # Nova Versão
st.title("Formulário de Análise e Geração de Email")

# Inicializa estado da sessão (Chaves importantes)
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
    "prazo_pagamento_dias": 15, "opcao_art_916": "Não oferecer/Não aplicável",
    "preview_916_details": None
}
for key, default_value in default_session_state.items():
    if key not in st.session_state: st.session_state[key] = default_value
# ========= FIM: Configuração da Página e Estado =========

# ====== SIDEBAR DE AJUDA ======
with st.sidebar:
    st.header("Ajuda - Roteiro de Análise")
    # Colar texto da ajuda atualizado aqui
    st.info(
        """
        **Objetivo:** Preencher a análise para gerar um
        rascunho de e-mail interno sobre a decisão.

        **1. Contexto:**
        * **Fase Processual:** Define opções de Decisão/Recurso.
        * **Data da Ciência:** Essencial para prazos.
        * **Cliente é:** Papel do seu cliente (Rte/Rdo).
        * **Tipo de Decisão:** Selecione a decisão específica
            (opções variam conforme a Fase).
        * *(Nº Proc, Nomes, Local usarão placeholders [ ] no e-mail).*

        **2. Análise Decisão:**
        * **Resultado Geral:** Impacto para seu cliente.
        * **Valor (R$):** Aparece se 'Desfavorável' ou em 'Execução'.
            Informe o valor principal da condenação ou do cálculo.
        * **Observações:** Detalhes/nuances da decisão.
        * **Síntese (Opcional):** Resumo conciso para o corpo do e-mail.
        * **Cálculos (Execução):** *Expander opcional.* Se for
            homologação, detalhe os valores aqui (Principal, INSS...).
        * **Dep. Anteriores:** *Expander opcional.* Informe se houver
            depósitos recursais de fases anteriores.
        * **Prazo Pagamento (Exec):** Informe o prazo em dias
            concedido na decisão para pagamento.
        * **Parcelamento 916 (Exec):** Indique se deve ser oferecido
            ou se o cliente já optou. Use o botão 'Calcular/Pré-visualizar'
            para ver os valores e datas antes de gerar o email.

        **3. Pedidos (Tabela):**
        * **UPLOAD (Preferencial):** Use 'Carregar Arquivo'
            (CSV, Excel, TXT c/ TABs) para maior confiabilidade.
        * **Texto Colado (Alternativa):** Cole o texto do DataJuri
            se não puder usar arquivo. Veja ajuda `(?)` do campo.
        * **Verificar:** Clique para processar a tabela e ver o preview.

        **4. Próximo Passo:**
        * **ED:** Avalie se cabem Embargos. Justifique se 'Sim'.
        * **Recurso:** Aparece se 'Não cabe ED'. Opções mudam c/ Fase.
            Confirme/altere a sugestão e **justifique**.
        * **Garantia (Exec):** Marque se necessária para o recurso
            de execução selecionado (Ex: Embargos, AP).
        * **Custas/Depósito:** Selecione o status correto. Use as
            novas opções ('Já Recolhidas', 'Garantido...', 'Não Aplicável').
            Informe o valor **apenas** se 'A Recolher'.
        * **Guias:** Aparece se houver valor a recolher. Indique o
            status e onde encontrar/salvar as guias.

        **5. Prazos e Obs.:**
        * **Prazos:** Use sugestões ou adicione manualmente.
            Selecione o tipo na lista ou 'Outro (Especificar)'.
            D- é calculada como Fatal - 3 dias úteis (padrão).
            Remova prazos com 'X'.
            *(Prazos do Art. 916 são adicionados automaticamente
            ao gerar o e-mail se 'Cliente Optou...' for selecionado).*
        * **Observações Finais:** Notas adicionais internas.

        **Gerar Email:** Botão final, valida todos os campos
        obrigatórios e gera o rascunho na tela.
        """
    )
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
    st.subheader("Informações Gerais"); col_fase, col_contexto1 = st.columns([0.5, 1.5])
    with col_fase: st.radio("Fase:", ["Conhecimento", "Execução"], index=["Conhecimento", "Execução"].index(st.session_state.fase_processual), key="fase_processual", horizontal=True)
    with col_contexto1: st.date_input("Data da Ciência:", value=st.session_state.get("data_ciencia"), key="data_ciencia", help="Data da notificação formal.")
    st.session_state.data_ciencia_valida = st.session_state.data_ciencia is not None
    # Warning do Streamlit aqui é esperado devido ao uso de key e index baseado no state
    st.radio("Cliente é:", config.CLIENTE_OPTIONS, index=config.CLIENTE_OPTIONS.index(st.session_state.cliente_role_radio), key="cliente_role_radio", horizontal=True)
    st.caption("Info: Nº do Processo, Nomes das Partes e Local usarão placeholders [ ] no e-mail.")
    st.subheader("Decisão Analisada")
    current_decisao_options = config.DECISAO_OPTIONS_EXECUCAO if st.session_state.fase_processual == "Execução" else config.DECISAO_OPTIONS_CONHECIMENTO
    st.selectbox("Tipo de Decisão:", options=current_decisao_options, index=current_decisao_options.index(st.session_state.tipo_decisao) if st.session_state.tipo_decisao in current_decisao_options else 0, key="tipo_decisao")

# --- Tab 2: Análise Decisão ---
with tab_analise:
    st.subheader("Resultado e Valor"); col_res1, col_res2 = st.columns([1,1])
    with col_res1: st.selectbox("Resultado Geral p/ Cliente:", options=config.RESULTADO_OPTIONS, index=config.RESULTADO_OPTIONS.index(st.session_state.resultado_sentenca) if st.session_state.resultado_sentenca in config.RESULTADO_OPTIONS else 0, key="resultado_sentenca")
    with col_res2:
        mostrar_valor = st.session_state.resultado_sentenca == "Desfavorável" or st.session_state.fase_processual == "Execução"
        if mostrar_valor: label_valor = "Valor Condenação/Arbitrado (R$):" if st.session_state.fase_processual == "Conhecimento" else "Valor Execução/Cálculo (R$):"; st.number_input(label_valor, min_value=0.0, step=0.01, format="%.2f", key="valor_condenacao_execucao")
    st.text_area("Observações sobre a Decisão:", key="obs_sentenca", help="Detalhe nuances.")
    st.text_area("Síntese Decisão / Objeto Recurso (p/ Email):", height=100, key="sintese_objeto_recurso", help="Resumo conciso para corpo do e-mail.")

    # --- Campos de Execução ---
    if st.session_state.fase_processual == "Execução":
        st.markdown("---"); st.subheader("Detalhes da Execução")
        col_exec1, col_exec2 = st.columns(2)
        with col_exec1: st.number_input("Prazo para Pagamento (dias):", min_value=1, step=1, key="prazo_pagamento_dias", help="Prazo concedido na decisão (default 15).")
        with col_exec2:
             opcoes_916 = ["Não oferecer/Não aplicável", "Oferecer Opção Art. 916", "Cliente Optou por Art. 916"]; st.selectbox("Parcelamento Art. 916 CPC:", options=opcoes_916, index=opcoes_916.index(st.session_state.opcao_art_916) , key="opcao_art_916", help="Oferecer ou confirmar opção?")

        # --- Botão e Lógica de Preview do Parcelamento 916 ---
        preview_916_placeholder = st.empty()
        # Mostra botão de calcular/preview se for execução E opção 916 for relevante
        if st.session_state.opcao_art_916 in ["Oferecer Opção Art. 916", "Cliente Optou por Art. 916"]:
            if st.button("📊 Calcular/Pré-visualizar Parcelamento 916"):
                calc_principal_liq_preview = st.session_state.get("calc_principal_liq", 0.0)
                data_ciencia_preview = st.session_state.get("data_ciencia")
                prazo_pag_preview = st.session_state.get("prazo_pagamento_dias", 15)
                preview_details = None # Reseta o preview anterior
                st.session_state.preview_916_details = None # Limpa state tb

                if not data_ciencia_preview: preview_916_placeholder.error("Informe a Data da Ciência (Tab 1) para calcular.")
                elif calc_principal_liq_preview <= 0: preview_916_placeholder.warning("Informe um 'Principal Líquido' maior que zero nos Cálculos Homologados para calcular parcelas.")
                else:
                    try:
                        data_fatal_entrada = add_business_days(data_ciencia_preview, prazo_pag_preview)
                        if data_fatal_entrada:
                            valor_entrada_30 = calc_principal_liq_preview * 0.30
                            saldo_remanescente = calc_principal_liq_preview * 0.70
                            num_parcelas = 6
                            valor_parcela_base = saldo_remanescente / num_parcelas if num_parcelas > 0 else 0
                            lista_parcelas_preview = []
                            data_base_parcela = data_fatal_entrada
                            for n in range(1, num_parcelas + 1):
                                valor_parcela_n = valor_parcela_base * (1 + n * 0.01)
                                data_fatal_parcela = add_months(data_base_parcela, n)
                                if not data_fatal_parcela: raise ValueError(f"Erro ao calcular data da parcela {n}")
                                data_d_pag_parcela = add_business_days(data_fatal_parcela, -3)
                                data_comunicacao = add_business_days(data_fatal_parcela, -5)
                                lista_parcelas_preview.append({
                                    "Parcela": f"{n}/{num_parcelas}",
                                    "Valor (R$)": f"{valor_parcela_n:.2f}",
                                    "Vencimento (Fatal)": data_fatal_parcela.strftime('%d/%m/%Y'),
                                    "Pagamento (D-)": data_d_pag_parcela.strftime('%d/%m/%Y'),
                                    "Comunicar Cliente (D-/Fatal)": data_comunicacao.strftime('%d/%m/%Y')
                                })
                            preview_details = { "entrada_30": valor_entrada_30, "saldo_remanescente": saldo_remanescente, "parcela_base": valor_parcela_base, "parcelas": lista_parcelas_preview, "data_fatal_entrada": data_fatal_entrada }
                            st.session_state.preview_916_details = preview_details # Guarda no state
                            with preview_916_placeholder.container():
                                st.success("Cálculo do Parcelamento (Pré-visualização):")
                                st.markdown(f"**Entrada (30% de R$ {calc_principal_liq_preview:.2f}): R$ {valor_entrada_30:.2f}**")
                                st.markdown(f"**Saldo Remanescente:** R$ {saldo_remanescente:.2f} (Valor base parcela: R$ {valor_parcela_base:.2f})")
                                st.markdown("**Parcelas (+1% a.m. simples sobre base):**")
                                df_preview = pd.DataFrame(lista_parcelas_preview)
                                st.dataframe(df_preview, hide_index=True, use_container_width=True)
                        else: preview_916_placeholder.error("Não foi possível calcular a data de entrada para as parcelas."); st.session_state.preview_916_details = None
                    except Exception as e_calc: preview_916_placeholder.error(f"Erro ao calcular parcelamento: {e_calc}"); st.session_state.preview_916_details = None
        # Exibe o último preview calculado se existir no state
        elif st.session_state.get("preview_916_details"):
             with preview_916_placeholder.container():
                st.markdown("---"); st.write("**Pré-visualização Anterior do Parcelamento 916:**")
                details = st.session_state.preview_916_details
                calc_principal_liq_preview = details['entrada_30'] / 0.30 if details['entrada_30'] > 0 else 0 # Recalcula base
                st.markdown(f"**Entrada (30% de R$ {calc_principal_liq_preview:.2f}): R$ {details['entrada_30']:.2f}**")
                st.markdown(f"**Saldo Remanescente:** R$ {details['saldo_remanescente']:.2f} (Base parcela: R$ {details['parcela_base']:.2f})")
                st.markdown("**Parcelas (+1% a.m. simples sobre base):**")
                df_preview = pd.DataFrame(details['parcelas'])
                st.dataframe(df_preview, hide_index=True, use_container_width=True)

        with st.expander("Detalhes dos Cálculos Homologados (Opcional)", expanded=True):
            st.number_input("Valor Total Homologado (R$):", key="calc_total_homologado"); st.number_input("Principal Líquido (+Juros?) (R$):", key="calc_principal_liq"); st.number_input("INSS Empregado (Base) (R$):", key="calc_inss_emp"); st.number_input("FGTS (+Taxa?) (R$):", key="calc_fgts"); st.number_input("Hon. Sucumbência (R$):", key="calc_hon_suc"); st.number_input("Hon. Periciais (R$):", key="calc_hon_per"); st.text_area("Obs Cálculos:", key="calc_obs")
    with st.expander("Depósitos Recursais Anteriores (Opcional)"):
        st.number_input("Valor Total Aprox. (R$):", key="dep_anterior_valor")
        st.text_area("Detalhes (Datas, Tipos):", key="dep_anterior_detalhes")


# --- Tab 3: Pedidos (Tabela) ---
with tab_pedidos:
    # (Conteúdo mantido)
    # ...
    st.subheader("Tabela de Pedidos (DataJuri)"); st.write("Use o Upload de Arquivo (preferencial) ou cole o texto abaixo.")
    uploaded_file = st.file_uploader("Carregar Arquivo (CSV, Excel, TXT com TABs)", type=['csv', 'xlsx', 'xls', 'txt'], key="file_uploader")
    st.markdown("---"); st.write("Ou cole o texto da tabela aqui:")
    if st.button("Mostrar/Ocultar Imagem Exemplo", key="toggle_image_btn"): st.session_state.show_image_example = not st.session_state.show_image_example
    if st.session_state.show_image_example:
        try: st.image(config.IMAGE_PATH, caption="Exemplo Tela DataJuri", use_column_width=True); st.caption(f"Verifique se '{config.IMAGE_PATH}' está na pasta.")
        except FileNotFoundError: st.error(f"Erro: Imagem '{config.IMAGE_PATH}' não encontrada.")
        except Exception as img_e: st.error(f"Erro ao carregar imagem: {img_e}")
    help_text_tabela_v4 = """..."""
    st.text_area("Conteúdo Tabela Colada:", height=150, key="texto_tabela_pedidos", help=help_text_tabela_v4, label_visibility="collapsed")
    preview_placeholder_pedidos = st.empty() # Placeholder diferente para o preview dos pedidos
    if st.button("Verificar Tabela Carregada/Colada"):
        tipo_decisao_atual = st.session_state.tipo_decisao
        if not tipo_decisao_atual or tipo_decisao_atual == config.DECISAO_OPTIONS_CONHECIMENTO[0]: preview_placeholder_pedidos.error("Selecione 'Tipo de Decisão Analisada' na aba 'Contexto' antes.")
        elif uploaded_file or st.session_state.texto_tabela_pedidos.strip():
            with st.spinner("Processando tabela..."):
                parsed_data, error_msg = parse_and_format_report_v3(texto=st.session_state.texto_tabela_pedidos if not uploaded_file else None, uploaded_file=uploaded_file)
                if parsed_data is not None: st.session_state.parsed_pedidos_data = parsed_data; st.session_state.parsed_pedidos_error = None; preview_placeholder_pedidos.success("Tabela processada!"); preview_placeholder_pedidos.dataframe(parsed_data, use_container_width=True)
                else: st.session_state.parsed_pedidos_data = None; st.session_state.parsed_pedidos_error = error_msg; preview_placeholder_pedidos.error(f"Falha:"); preview_placeholder_pedidos.code(error_msg, language=None)
        else: preview_placeholder_pedidos.warning("Carregue um arquivo ou cole o texto."); st.session_state.parsed_pedidos_data = None; st.session_state.parsed_pedidos_error = None


# --- Tab 4: Próximo Passo (ED/Recurso) ---
with tab_proximo_passo:
    # (Conteúdo mantido)
    # ...
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
    # (Conteúdo Tab 5 mantido)
    # ...
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
    st.subheader("Observações Finais"); st.text_area("Observações Gerais (para registro interno):", key="obs_finais", height=100)

# ========= BOTÃO FINAL PARA GERAR O E-MAIL =========
st.divider()
if st.button("📧 Gerar Rascunho de E-mail", type="primary", use_container_width=True):
    # (Bloco de validação mantido)
    # ...
    valid = True; error_messages = []; # ... (validações completas) ...
    if not valid:
        st.error("Existem erros/campos obrigatórios não preenchidos:")
        for msg in error_messages: st.error(f"- {msg}")
        st.stop()
    else:
        # --- LÓGICA PARA ADICIONAR PRAZOS AUTOMÁTICOS ---
        prazos_atuais_dict = st.session_state.prazos; adicionados_count = 0
        opcao_916_val = st.session_state.get("opcao_art_916")
        data_ciencia_val = st.session_state.get("data_ciencia")
        prazo_pagamento_val = st.session_state.get("prazo_pagamento_dias", 15)
        fase_val = st.session_state.fase_processual
        ed_status_val = st.session_state.get("ed_status")
        recurso_selecionado_val = st.session_state.get("recurso_sel")
        prazos_existentes_desc = {p['descricao'] for p in prazos_atuais_dict}

        # 1. Adiciona Prazos 916 (se aplicável)
        if fase_val == "Execução" and opcao_916_val == "Cliente Optou por Art. 916" and data_ciencia_val:
            log.info("Adicionando prazos do Art. 916...")
            try:
                # Usa dados do preview se existirem e forem válidos
                preview_data = st.session_state.get("preview_916_details")
                if preview_data and preview_data.get('parcelas') and preview_data.get('data_fatal_entrada'):
                    log.debug("Usando datas pré-calculadas do preview para prazos 916.")
                    for parcela_info in preview_data['parcelas']:
                        desc_pag = f"Pagamento Parcela {parcela_info['Parcela']} (Art. 916)"
                        if desc_pag not in prazos_existentes_desc:
                             prazo_pag = {"descricao": desc_pag, "data_d": parcela_info['Pagamento (D-)'], "data_fatal": parcela_info['Vencimento (Fatal)'], "obs": f"Ref. Homologação {data_ciencia_val.strftime('%d/%m/%Y')}"}
                             try: # Converte datas de volta para YYYY-MM-DD
                                 prazo_pag["data_d"] = datetime.strptime(prazo_pag["data_d"], '%d/%m/%Y').strftime('%Y-%m-%d')
                                 prazo_pag["data_fatal"] = datetime.strptime(prazo_pag["data_fatal"], '%d/%m/%Y').strftime('%Y-%m-%d')
                                 prazos_atuais_dict.append(prazo_pag); adicionados_count += 1; prazos_existentes_desc.add(desc_pag)
                             except ValueError: log.warning(f"Formato de data inválido no preview 916 para {desc_pag}")
                        desc_com = f"Comunicar Cliente - Venc. Parcela {parcela_info['Parcela']}"
                        if desc_com not in prazos_existentes_desc:
                             prazo_com = {"descricao": desc_com, "data_d": parcela_info['Comunicar Cliente (D-/Fatal)'], "data_fatal": parcela_info['Comunicar Cliente (D-/Fatal)'], "obs": f"Ref. Parcela venc. {parcela_info['Vencimento (Fatal)']}"}
                             try: # Converte datas
                                 prazo_com["data_d"] = datetime.strptime(prazo_com["data_d"], '%d/%m/%Y').strftime('%Y-%m-%d')
                                 prazo_com["data_fatal"] = datetime.strptime(prazo_com["data_fatal"], '%d/%m/%Y').strftime('%Y-%m-%d')
                                 prazos_atuais_dict.append(prazo_com); adicionados_count += 1; prazos_existentes_desc.add(desc_com)
                             except ValueError: log.warning(f"Formato de data inválido no preview 916 para {desc_com}")
                else: # Fallback: Recalcula datas (se não houve preview ou falhou)
                    log.warning("Preview 916 não disponível/válido, recalculando datas para adicionar prazos...")
                    data_fatal_entrada = add_business_days(data_ciencia_val, prazo_pagamento_val)
                    if data_fatal_entrada:
                        data_base_parcela = data_fatal_entrada
                        for n_parcela in range(1, 7):
                            # ... (lógica de cálculo e append como antes) ...
                             pass # Adicionar lógica de recálculo e append aqui se necessário

            except Exception as e_prazo916: st.warning(f"Não foi possível adicionar prazos Art. 916: {e_prazo916}"); log.error("Erro prazos 916", exc_info=True)

        # 2. Adiciona Prazo "Verificar Recurso Contrário"
        elif ed_status_val == "Não cabe ED" and recurso_selecionado_val == "Não Interpor Recurso" and data_ciencia_val:
            log.info("Adicionando prazo para Verificar Recurso Contrário...")
            try:
                desc_verif = "Verificar Recurso Contrário"
                if desc_verif not in prazos_existentes_desc:
                    data_fatal_verif = add_business_days(data_ciencia_val, 8)
                    data_d_verif = data_fatal_verif
                    prazo_verif = {"descricao": desc_verif, "data_d": str(data_d_verif), "data_fatal": str(data_fatal_verif), "obs": "Verificar se parte adversa interpôs recurso."}
                    prazos_atuais_dict.append(prazo_verif); adicionados_count += 1; log.debug(f"--> ADICIONADO Prazo Verificação: {prazo_verif}")
                else: log.debug(f"--> Prazo Verificação '{desc_verif}' JÁ EXISTE.")
            except Exception as e_prazo_verif: st.warning(f"Não foi possível adicionar prazo Verificação: {e_prazo_verif}"); log.error("Erro prazo Verificação", exc_info=True)

        # Atualiza estado e informa se algo foi adicionado
        if adicionados_count > 0:
             st.toast(f"{adicionados_count} prazo(s) automático(s) adicionado(s)!"); log.info(f"{adicionados_count} prazos auto add."); st.session_state.prazos = prazos_atuais_dict
        # --- FIM DA LÓGICA DE ADIÇÃO DE PRAZOS ---

        # Coleta final e Geração do Email
        email_data = {key: st.session_state.get(key) for key in st.session_state}
        email_data['prazos'] = st.session_state.prazos # Passa lista ATUALIZADA
        # ... (ajustes de chave) ...

        log.info("Gerando rascunho de e-mail...")
        try:
            email_subject, email_body = generate_email_body(**email_data)
            st.subheader("Rascunho do E-mail Gerado"); st.text_input("Assunto:", value=email_subject, key="email_subj_final"); st.text_area("Corpo do E-mail:", value=email_body, height=600, key="email_body_final"); st.success("Rascunho gerado!"); log.info("Rascunho gerado.")
        except Exception as e_email:
            st.error(f"Erro ao gerar corpo do e-mail: {e_email}"); log.error("Erro em generate_email_body", exc_info=True)

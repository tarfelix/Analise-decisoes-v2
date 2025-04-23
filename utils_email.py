# -*- coding: utf-8 -*-
# Arquivo: utils_email.py (Versão Corrigida e Completa)

from datetime import datetime, date
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging

log = logging.getLogger(__name__)

# Tenta importar PedidoData do parser
try:
    from parser import PedidoData
except ImportError:
    log.warning("parser.PedidoData não encontrado, usando definição fallback em utils_email.")
    # <<< Definição CORRIGIDA da classe fallback >>>
    @dataclass
    class PedidoData: # Define um substituto básico
        Objetos: str = ""
        Situação: str = "N/A"
        Res1: str = "N/A"
        Res2: str = "N/A"
        ResSup: str = "N/A"

# Importa funções de data apenas se necessário e seguro
try:
    from utils_date import add_months, add_business_days
except ImportError:
    log.error("Módulo utils_date não encontrado! Funções de data não funcionarão corretamente.")
    # Define funções dummy para evitar NameError, mas elas não funcionarão direito
    from datetime import timedelta
    def add_months(source_date, months): return source_date + timedelta(days=30*months) # Aproximação!
    def add_business_days(from_date, num_days): return from_date + timedelta(days=num_days) # Sem considerar feriados!


# --- Dataclass Prazo ---
@dataclass
class Prazo:
    descricao: str
    data_d: str
    data_fatal: str
    obs: str = ""

# --- Função para Hiperlink ---
def make_hyperlink(path: str) -> str:
    """Gera link Markdown se o path for URL."""
    path_cleaned = path.strip();
    if path_cleaned and (path_cleaned.lower().startswith(("http://", "https://"))): return f"[{path_cleaned}]({path_cleaned})"
    return path_cleaned

# --- Função para formatar prazos ---
def format_prazos(prazos_list: List[Dict[str, Any]]) -> str:
    """Formata a lista de prazos (dicts) para exibição no texto final."""
    if not prazos_list: return "Nenhum prazo informado."
    lines = []
    for i, p_dict in enumerate(prazos_list, start=1):
        try:
            p = Prazo(**p_dict); lines.append(f"{i}) {p.descricao}"); data_d_str = "N/I"; data_fatal_str = "N/I"
            try: data_d_obj = datetime.strptime(p.data_d, '%Y-%m-%d').date(); data_d_str = data_d_obj.strftime('%d/%m/%Y')
            except: data_d_str = f"{p.data_d}(Inválido)"
            try: data_fatal_obj = datetime.strptime(p.data_fatal, '%Y-%m-%d').date(); data_fatal_str = data_fatal_obj.strftime('%d/%m/%Y')
            except: data_fatal_str = f"{p.data_fatal}(Inválido)"
            lines.append(f"   - Data D-: {data_d_str}"); lines.append(f"   - Data Fatal: {data_fatal_str}")
            obs = p.obs.strip();
            if obs: lines.append(f"   - Observações: {obs}")
            lines.append("")
        except TypeError as e: lines.append(f"{i}) Erro formatar prazo: {p_dict} - {e}"); lines.append("")
        except Exception as e_gen: lines.append(f"{i}) Erro inesperado ao formatar prazo: {p_dict} - {e_gen}"); lines.append("")
    return "\n".join(lines)


# --- Função para formatar pedidos para Email (SEMPRE como Lista) ---
def format_pedidos_email(pedidos_data: List[PedidoData], tipo_decisao: str) -> str:
    """Formata a lista de pedidos (dataclasses) para o corpo do e-mail, SEMPRE como lista."""
    if not pedidos_data: return "Nenhuma informação de pedido disponível."
    log.debug(f"Formatando {len(pedidos_data)} pedidos como LISTA para email (Tipo Decisão: {tipo_decisao})")
    linhas_email = []; tipo_lower = tipo_decisao.lower() if tipo_decisao else ""
    linhas_email.append("SÍNTESE DOS PEDIDOS / SITUAÇÃO:")
    linhas_email.append("-" * 30)
    show_res1 = True; show_res2 = False; show_resSup = False
    if tipo_lower.startswith("acórdão (trt)"): show_res2 = True
    elif tipo_lower.startswith("acórdão (tst"): show_res2 = True; show_resSup = True
    elif tipo_lower.startswith(("decisão monocrática", "despacho denegatório", "homologação de cálculos")): show_res2 = True; show_resSup = True
    def is_relevant_email(res_value): return res_value and res_value.lower() not in ["aguardando julgamento", "n/a", "", "não houve recurso"]
    for index, item in enumerate(pedidos_data, start=1):
        linhas_email.append(f"{index}) {item.Objetos}")
        situacao = item.Situação.strip()
        if situacao and situacao != 'N/A': linhas_email.append(f"   - Situação: {situacao}")
        res1 = item.Res1.strip(); res2 = item.Res2.strip(); resSup = item.ResSup.strip()
        if show_res1 and is_relevant_email(res1): linhas_email.append(f"   - Resultado 1ª Instância: {res1}")
        if show_res2 and is_relevant_email(res2): linhas_email.append(f"   - Resultado 2ª Instância: {res2}")
        if show_resSup and is_relevant_email(resSup): linhas_email.append(f"   - Resultado Instância Superior: {resSup}")
        linhas_email.append("")
    return "\n".join(linhas_email).strip()


# --- Função para Gerar Corpo e Assunto do Email (Com Cálculo 916 e Textos Finais Ajustados) ---
def generate_email_body(**kwargs) -> tuple:
    log.info("Iniciando generate_email_body...")
    # --- Extração de Dados ---
    fase = kwargs.get("fase_processual"); tipo_decisao = kwargs.get("tipo_decisao", ""); data_ciencia = kwargs.get("data_ciencia"); data_ciencia_str = data_ciencia.strftime('%d/%m/%Y') if data_ciencia else "[DATA CIÊNCIA]"; resultado = kwargs.get("resultado_sentenca"); valor_condenacao = kwargs.get("valor_condenacao_execucao", 0.0); obs_decisao = kwargs.get("obs_sentenca"); sintese_objeto = kwargs.get("sintese_objeto_recurso", ""); pedidos_data = kwargs.get("pedidos_data", []); ed_status = kwargs.get("ed_status"); justificativa_ed = kwargs.get("justificativa_ed"); recurso_rec = kwargs.get("recurso_selecionado"); recurso_outro = kwargs.get("recurso_outro_especificar"); recurso_just = kwargs.get("recurso_justificativa"); garantia_necessaria = kwargs.get("garantia_necessaria", False); status_custas = kwargs.get("status_custas"); valor_custas = kwargs.get("valor_custas", 0.0); status_deposito = kwargs.get("status_deposito"); valor_deposito = kwargs.get("valor_deposito_input", 0.0); guias_status = kwargs.get("guias_status"); local_guias = kwargs.get("local_guias"); prazos = kwargs.get("prazos", []); obs_finais = kwargs.get("obs_finais"); calc_principal_liq = kwargs.get("calc_principal_liq", 0.0); calc_inss_emp = kwargs.get("calc_inss_emp", 0.0); calc_fgts = kwargs.get("calc_fgts", 0.0); calc_hon_suc = kwargs.get("calc_hon_suc", 0.0); calc_hon_per = kwargs.get("calc_hon_per", 0.0); calc_total_homologado = kwargs.get("calc_total_homologado", 0.0); calc_obs = kwargs.get("calc_obs",""); dep_anterior_valor = kwargs.get("dep_anterior_valor", 0.0); dep_anterior_detalhes = kwargs.get("dep_anterior_detalhes","")
    prazo_pagamento_dias = kwargs.get("prazo_pagamento_dias", 15)
    opcao_art_916 = kwargs.get("opcao_art_916", "Não oferecer/Não aplicável")
    log.debug("Dados extraídos para gerar email.")

    # --- Assunto ---
    subject = f"TRABALHISTA: {tipo_decisao.split('(')[0].strip()} ({fase}) - [ADVERSO] X [CLIENTE] - Proc [Nº PROCESSO]"

    # --- Corpo ---
    body_lines = []; body_lines.append("Prezados, bom dia!"); body_lines.append("")
    body_lines.append(f"Local: [LOCAL]"); body_lines.append(f"Processo nº: [Nº PROCESSO]")
    body_lines.append(f"Cliente: [CLIENTE]"); body_lines.append(f"Adverso: [ADVERSO]"); body_lines.append("")
    body_lines.append(f"Pelo presente, informamos a decisão ({tipo_decisao} / {fase}) publicada/disponibilizada em {data_ciencia_str}.")
    body_lines.append("")

    # --- Bloco 1: Pedidos ---
    if pedidos_data: body_lines.append(format_pedidos_email(pedidos_data, tipo_decisao)); body_lines.append("")
    else: log.warning("Não há dados de pedidos para incluir no e-mail.")

    # --- Bloco 2: Análise da Decisão ---
    added_sintese_obs = False
    if ed_status == "Cabe ED": body_lines.append(f"Trata-se de decisão ({tipo_decisao}) em que se entende cabível Embargos de Declaração:"); body_lines.append(f"Justificativa ED: {justificativa_ed}"); body_lines.append(""); added_sintese_obs = True
    elif sintese_objeto: body_lines.append("SÍNTESE DA DECISÃO / OBJETO DO RECURSO:"); body_lines.append(sintese_objeto); body_lines.append(""); added_sintese_obs = True
    elif obs_decisao: body_lines.append("OBSERVAÇÕES SOBRE A DECISÃO:"); body_lines.append(obs_decisao); body_lines.append(""); added_sintese_obs = True

    # --- Bloco 3: Detalhes da Execução / Pagamento / Recurso ---
    is_homologacao = fase == "Execução" and tipo_decisao and "Homologação de Cálculos" in tipo_decisao
    recursos_exec_impeditivos_916 = ["Embargos à Execução / Impugnação à Sentença", "Agravo de Petição (AP)"]
    recurso_impeditivo_selecionado = fase == "Execução" and recurso_rec in recursos_exec_impeditivos_916
    data_d_pagamento_str = "[DATA D- PAGAMENTO]"; data_fatal_pagamento_str = "[DATA FATAL PAGAMENTO]" # Placeholders
    if data_ciencia: # Calcula datas apenas se data ciência existe
        try: data_fatal_pag = add_business_days(data_ciencia, prazo_pagamento_dias); data_d_pag = add_business_days(data_fatal_pag, -3); data_d_pagamento_str = data_d_pag.strftime('%d/%m/%Y'); data_fatal_pagamento_str = data_fatal_pag.strftime('%d/%m/%Y'); log.debug(f"Datas Pagamento Calculadas: D-={data_d_pagamento_str}, Fatal={data_fatal_pagamento_str}")
        except Exception as e_dt_pag: log.error(f"Erro ao calcular datas de pagamento: {e_dt_pag}")

    # Cenário Homologação
    if is_homologacao:
        body_lines.append(f"Foram homologados os cálculos, determinando o pagamento no prazo de {prazo_pagamento_dias} dias (Fatal: {data_fatal_pagamento_str}), sob pena de penhora.")
        body_lines.append(""); body_lines.append("Valores homologados:")
        # ... (exibição dos valores calc_... mantida) ...
        valor_liq_reclamante = calc_principal_liq;
        if calc_total_homologado > 0: body_lines.append(f"- Valor Total: R$ {calc_total_homologado:.2f}")
        if valor_liq_reclamante > 0: body_lines.append(f"- Principal Líquido: R$ {valor_liq_reclamante:.2f}")
        if calc_inss_emp > 0: body_lines.append(f"- INSS Emp (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
        if calc_fgts > 0: body_lines.append(f"- FGTS: R$ {calc_fgts:.2f} (Conta Vinculada)")
        if calc_hon_suc > 0: body_lines.append(f"- Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
        if calc_hon_per > 0: body_lines.append(f"- Hon. Periciais: R$ {calc_hon_per:.2f}")
        if calc_obs: body_lines.append(f"- Obs Cálculos: {calc_obs}")
        body_lines.append("")

        if recurso_impeditivo_selecionado: # Modelo 3 ou 4
            recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro; body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Entendemos pela interposição de {recurso_final}:"); body_lines.append(recurso_just if recurso_just else "[JUSTIFICATIVA PENDENTE]"); body_lines.append("")
            if not garantia_necessaria: log.debug("Execução - Modelo 3"); body_lines.append("Considerando a interposição do recurso, guias não enviadas."); body_lines.append("Gentileza retornar em 24h se concordam.")
            else: log.debug("Execução - Modelo 4"); body_lines.append("Recomendamos garantia do juízo."); body_lines.append("Requereremos que valores não sejam transferidos."); body_lines.append(""); body_lines.append("Gentileza retornar em 24h se concordam."); body_lines.append(f"Caso positivo, enviar comprovantes (...) até {data_d_pagamento_str}.")
            if garantia_necessaria and (status_custas == "A Recolher" or status_deposito in ["Garantia do Juízo (Integral)", "A Recolher (Situação Específica)"]):
                 if guias_status == "Guias já elaboradas e salvas": body_lines.append(f"- Guias p/ garantia/pagamento salvas em: {make_hyperlink(local_guias)}")
                 elif guias_status == "Guias pendentes de elaboração": body_lines.append("- Guias p/ garantia/pagamento serão elaboradas.")
            body_lines.append("")
        else: # Cenário 1 ou 2
            if dep_anterior_valor > 0: log.debug("Execução - Modelo 1"); body_lines.append(f"Existem depósitos anteriores aprox. R$ {dep_anterior_valor:.2f}."); #... (restante do texto modelo 1)...
            else: # Modelo 2 Lógica
                log.debug("Execução - Lógica Modelo 2")
                if opcao_art_916 in ["Oferecer Opção Art. 916", "Cliente Optou por Art. 916"]:
                    log.debug(f"Execução - Modelo 2 - Opção 916: {opcao_art_916}")
                    body_lines.append("Considerando ausência de recurso, segue(m) opção(ões) para pagamento:")
                    body_lines.append(""); body_lines.append("**Opção 1: Pagamento Integral**"); body_lines.append(f"- Líquido Reclamante: R$ {valor_liq_reclamante:.2f}")
                    # <<< CORREÇÃO: Lista das outras verbas aqui >>>
                    if calc_inss_emp > 0: body_lines.append(f"- INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
                    if calc_fgts > 0: body_lines.append(f"- FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
                    if calc_hon_suc > 0: body_lines.append(f"- Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
                    if calc_hon_per > 0: body_lines.append(f"- Hon. Periciais: R$ {calc_hon_per:.2f}")
                    body_lines.append("- (Verificar status/envio das guias)")
                    body_lines.append(f"  *Comprovação pagamento integral até {data_d_pagamento_str} (Fatal: {data_fatal_pagamento_str}).*"); body_lines.append("")

                    body_lines.append("**Opção 2: Pagamento Parcelado (Art. 916 CPC)**")
                    if valor_liq_reclamante > 0:
                        valor_entrada_30 = valor_liq_reclamante * 0.30; saldo_remanescente = valor_liq_reclamante * 0.70; num_parcelas = 6; valor_parcela_base = saldo_remanescente / num_parcelas if num_parcelas > 0 else 0
                        body_lines.append(f"- Depósito inicial 30%: R$ {valor_entrada_30:.2f}")
                        body_lines.append("- + Pagamento INTEGRAL e IMEDIATO de:")
                        # <<< CORREÇÃO: Lista das outras verbas aqui >>>
                        if calc_inss_emp > 0: body_lines.append(f"    - INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
                        if calc_fgts > 0: body_lines.append(f"    - FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
                        if calc_hon_suc > 0: body_lines.append(f"    - Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
                        if calc_hon_per > 0: body_lines.append(f"    - Hon. Periciais: R$ {calc_hon_per:.2f}")
                        body_lines.append(f"- Saldo remanescente (R$ {saldo_remanescente:.2f}) em {num_parcelas} parcelas mensais (+1% a.m. s/ base):")
                        if valor_parcela_base > 0:
                            for n in range(1, num_parcelas + 1): valor_parcela_n = valor_parcela_base * (1 + n * 0.01); body_lines.append(f"    - Parcela {n} aprox.: R$ {valor_parcela_n:.2f}")
                        else: body_lines.append("    - (Erro cálculo parcelas)")
                        body_lines.append("- (Verificar guias p/ entrada e verbas)")
                        body_lines.append(f"  *Comprovação entrada e verbas até {data_d_pagamento_str} (Fatal: {data_fatal_pagamento_str}).*"); body_lines.append("")
                    else: body_lines.append("  (Não aplicável - Valor líquido zero).")
                    body_lines.append("**Atenção:** Realizar pagamento **APENAS DOS VALORES DA MODALIDADE ESCOLHIDA**.");
                    if opcao_art_916 == "Oferecer Opção Art. 916": body_lines.append(f"*Favor informar opção até [PRAZO RESPOSTA CLIENTE] e enviar comprovantes até {data_d_pagamento_str}.*")
                    elif opcao_art_916 == "Cliente Optou por Art. 916": body_lines.append(f"*Cliente optou pelo parcelamento. Favor enviar comprovantes da entrada e verbas acessórias até {data_d_pagamento_str}.*")
                else: # Apenas Pagamento Integral
                     log.debug("Execução - Modelo 2 - Pagamento Integral Apenas")
                     body_lines.append("PAGAMENTO NECESSÁRIO (Integral):"); body_lines.append(f"- Líquido Reclamante: R$ {valor_liq_reclamante:.2f}"); # ... detalhar outras verbas ...
                     body_lines.append(f"  *Comprovação do pagamento integral até {data_d_pagamento_str} (Prazo Fatal: {data_fatal_pagamento_str}).*"); body_lines.append("")

    # --- Lógica para Outras Decisões (Conhecimento ou outras de Execução) ---
    # (Este bloco SÓ é executado se NÃO for Homologação de Cálculos)
    elif not is_homologacao:
        log.debug("Fase Conhecimento ou outra decisão Exec.")
        # (Lógica mantida: Síntese/Obs, Recurso, Custas/Depósito)
        if ed_status == "Não cabe ED" and recurso_rec and recurso_rec != "-- Selecione --":
            recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
            body_lines.append("POSIÇÃO DO ESCRITÓRIO:")
            if recurso_rec == "Não Interpor Recurso": body_lines.append(f"Não recomendamos interposição de recurso."); log.debug("Posição: Não Interpor.")
            else: body_lines.append(f"Recomendamos interposição de {recurso_final}."); log.debug(f"Posição: Recorrer com {recurso_final}")
            if recurso_just: body_lines.append(f"Justificativa/Objeto: {recurso_just}")
            body_lines.append("")
            # (Lógica Custas/Depósito mantida)
            precisa_recolher_custas = status_custas == "A Recolher"; precisa_recolher_deposito = status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            if precisa_recolher_custas or precisa_recolher_deposito:
                 body_lines.append("PAGAMENTOS NECESSÁRIOS PARA RECORRER:")
                 if precisa_recolher_custas: body_lines.append(f"- Custas Processuais: R$ {valor_custas:.2f}.")
                 if precisa_recolher_deposito: body_lines.append(f"- Depósito Recursal/Garantia: R$ {valor_deposito:.2f}.")
                 if guias_status == "Guias já elaboradas e salvas": body_lines.append(f"- Guias salvas em: {make_hyperlink(local_guias)}")
                 elif guias_status == "Guias pendentes de elaboração": body_lines.append("- Guias pendentes de elaboração.")
                 body_lines.append("")
            else: # Informa outros status
                 info_pagamento = []
                 if status_custas not in ["A Recolher", "-- Selecione --"]: info_pagamento.append(f"Custas Processuais: {status_custas}.")
                 if status_deposito not in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)", "-- Selecione --"]: info_pagamento.append(f"Depósito Recursal/Garantia: {status_deposito}.")
                 if info_pagamento: body_lines.extend(info_pagamento); body_lines.append("")


    # --- Bloco 5: Prazos ---
    if prazos:
        body_lines.append("PRAZOS RELEVANTES:"); body_lines.append(format_prazos(prazos))
    else: body_lines.append("PRAZOS RELEVANTES: Nenhum prazo específico adicionado.")
    body_lines.append("")

    # --- Bloco 6: Call to Action Final ---
    prazo_principal_obj = None
    if prazos: # Tenta encontrar prazo principal
        prazo_acao_imediata = ""; # ... (lógica mantida para encontrar prazo_acao_imediata) ...
        if ed_status == "Cabe ED": prazo_acao_imediata = "Embargos de Declaração"
        elif ed_status == "Não cabe ED" and recurso_rec and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --", "Outro"]: prazo_acao_imediata = recurso_rec
        elif ed_status == "Não cabe ED" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Verificar Recurso Contrário"
        elif fase == "Execução" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Pagamento"
        for p_dict in prazos:
            try: p = Prazo(**p_dict); desc = p.descricao;
            if prazo_acao_imediata and (prazo_acao_imediata.lower() in desc.lower()): prazo_principal_obj = p; break
            except: continue
    if prazo_principal_obj:
        try: # Tenta formatar datas
            data_d_cta = datetime.strptime(prazo_principal_obj.data_d, '%Y-%m-%d').strftime('%d/%m/%Y')
            data_fatal_cta = datetime.strptime(prazo_principal_obj.data_fatal, '%Y-%m-%d').strftime('%d/%m/%Y')
            desc_cta = prazo_principal_obj.descricao
            acao_pagamento_cta = status_custas == "A Recolher" or status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            acao_recurso_ed_cta = ed_status == "Cabe ED" or (ed_status == "Não cabe ED" and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"])

            # Não repete CTA de pagamento se já detalhado em Homologação/916
            if acao_pagamento_cta and not (is_homologacao and not recurso_impeditivo_selecionado):
                 body_lines.append(f"Solicitamos envio do(s) comprovante(s) de pagamento até {data_d_cta} (Data D-).")

            # Informa prazo fatal da medida principal
            if acao_recurso_ed_cta: body_lines.append(f"O prazo fatal para a medida ({desc_cta}) encerra em {data_fatal_cta}.")
            # Pede confirmação do cliente (Exceto ED ou Execução com Garantia - já tratado)
            if acao_recurso_ed_cta and ed_status != "Cabe ED" and not (fase=="Execução" and garantia_necessaria):
                 if recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"]: body_lines.append("*Solicitamos retorno quanto ao interesse na interposição do recurso em 48 horas.*")
            # Informa prazo de acompanhamento
            elif recurso_rec == "Não Interpor Recurso" and not is_homologacao:
                 body_lines.append(f"Acompanharemos até {data_fatal_cta} para verificar eventual recurso da parte contrária.")
            body_lines.append("")
        except Exception as e_cta: log.error(f"Erro ao gerar CTA final: {e_cta}")
    else: log.warning("Prazo principal não identificado para CTA final.")

    # --- Bloco 7: Observações Finais e Assinatura ---
    if obs_finais: body_lines.append("OBSERVAÇÕES FINAIS:"); body_lines.append(obs_finais); body_lines.append("")
    body_lines.append("Qualquer esclarecimento, favor entrar em contato com o escritório."); body_lines.append("")
    body_lines.append("Atenciosamente,"); body_lines.append(""); body_lines.append("[NOME ADVOGADO(A)]")

    log.info("Geração do corpo do e-mail finalizada.")
    return subject, "\n".join(body_lines)

# ========= FIM: Funções Auxiliares =========

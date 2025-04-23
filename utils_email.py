# -*- coding: utf-8 -*-
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
try: from parser import PedidoData
except ImportError: @dataclass class PedidoData: Objetos: str = ""; Situação: str = "N/A"; Res1: str = "N/A"; Res2: str = "N/A"; ResSup: str = "N/A"; log.warning("parser.PedidoData não encontrado.")
try: from utils_date import add_months, add_business_days
except ImportError: from datetime import timedelta; log.error("utils_date não encontrado!"); def add_months(s, m): return s + timedelta(days=30*m); def add_business_days(f, n): return f + timedelta(days=n)
import logging
log = logging.getLogger(__name__)

@dataclass
class Prazo: descricao: str; data_d: str; data_fatal: str; obs: str = ""

def make_hyperlink(path: str) -> str:
    """Gera link Markdown se o path for URL."""
    path_cleaned = path.strip();
    if path_cleaned and (path_cleaned.lower().startswith(("http://", "https://"))): return f"[{path_cleaned}]({path_cleaned})"
    return path_cleaned

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
    return "\n".join(lines)


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
    return "\n".join(linhas_email).strip() # Remove linha extra no final

# --- Função para Gerar Corpo e Assunto do Email (Revisada) ---
def generate_email_body(**kwargs) -> tuple:
    log.info("Iniciando generate_email_body...")
    # Extrai dados
    fase = kwargs.get("fase_processual"); tipo_decisao = kwargs.get("tipo_decisao", ""); data_ciencia = kwargs.get("data_ciencia"); data_ciencia_str = data_ciencia.strftime('%d/%m/%Y') if data_ciencia else "[DATA CIÊNCIA]"; resultado = kwargs.get("resultado_sentenca"); valor_condenacao = kwargs.get("valor_condenacao_execucao", 0.0); obs_decisao = kwargs.get("obs_sentenca"); sintese_objeto = kwargs.get("sintese_objeto_recurso", ""); pedidos_data = kwargs.get("pedidos_data", []); ed_status = kwargs.get("ed_status"); justificativa_ed = kwargs.get("justificativa_ed"); recurso_rec = kwargs.get("recurso_selecionado"); recurso_outro = kwargs.get("recurso_outro_especificar"); recurso_just = kwargs.get("recurso_justificativa"); garantia_necessaria = kwargs.get("garantia_necessaria", False); status_custas = kwargs.get("status_custas"); valor_custas = kwargs.get("valor_custas", 0.0); status_deposito = kwargs.get("status_deposito"); valor_deposito = kwargs.get("valor_deposito_input", 0.0); guias_status = kwargs.get("guias_status"); local_guias = kwargs.get("local_guias"); prazos = kwargs.get("prazos", []); obs_finais = kwargs.get("obs_finais"); calc_principal_liq = kwargs.get("calc_principal_liq", 0.0); calc_inss_emp = kwargs.get("calc_inss_emp", 0.0); calc_fgts = kwargs.get("calc_fgts", 0.0); calc_hon_suc = kwargs.get("calc_hon_suc", 0.0); calc_hon_per = kwargs.get("calc_hon_per", 0.0); calc_total_homologado = kwargs.get("calc_total_homologado", 0.0); calc_obs = kwargs.get("calc_obs",""); dep_anterior_valor = kwargs.get("dep_anterior_valor", 0.0); dep_anterior_detalhes = kwargs.get("dep_anterior_detalhes","")
    prazo_pagamento_dias = kwargs.get("prazo_pagamento_dias", 15)
    opcao_art_916 = kwargs.get("opcao_art_916", "Não oferecer/Não aplicável")
    log.debug("Dados extraídos para gerar email.")

    subject = f"TRABALHISTA: {tipo_decisao.split('(')[0].strip()} ({fase}) - [ADVERSO] X [CLIENTE] - Proc [Nº PROCESSO]"
    body_lines = []; body_lines.append("Prezados, bom dia!"); body_lines.append("")
    body_lines.append(f"Local: [LOCAL]"); body_lines.append(f"Processo nº: [Nº PROCESSO]")
    body_lines.append(f"Cliente: [CLIENTE]"); body_lines.append(f"Adverso: [ADVERSO]"); body_lines.append("")
    body_lines.append(f"Pelo presente, informamos a decisão ({tipo_decisao} / {fase}) publicada/disponibilizada em {data_ciencia_str}.")
    body_lines.append("")

    is_homologacao = fase == "Execução" and tipo_decisao and "Homologação de Cálculos" in tipo_decisao
    recursos_exec_impeditivos_916 = ["Embargos à Execução / Impugnação à Sentença", "Agravo de Petição (AP)"]
    recurso_impeditivo_selecionado = fase == "Execução" and recurso_rec in recursos_exec_impeditivos_916
    log.debug(f"Flags: is_homologacao={is_homologacao}, recurso_impeditivo_selecionado={recurso_impeditivo_selecionado}, opcao_art_916='{opcao_art_916}'")

    # --- Calcula datas de pagamento (se homologação) ---
    data_d_pagamento_str = "[DATA D- PAGAMENTO]"; data_fatal_pagamento_str = "[DATA FATAL PAGAMENTO]"
    if is_homologacao and data_ciencia:
        try: data_fatal_pag = add_business_days(data_ciencia, prazo_pagamento_dias); data_d_pag = add_business_days(data_fatal_pag, -3); data_d_pagamento_str = data_d_pag.strftime('%d/%m/%Y'); data_fatal_pagamento_str = data_fatal_pag.strftime('%d/%m/%Y'); log.debug(f"Datas Pagamento Calculadas: D-={data_d_pagamento_str}, Fatal={data_fatal_pagamento_str}")
        except Exception as e_dt_pag: log.error(f"Erro ao calcular datas de pagamento: {e_dt_pag}")

    # --- Bloco 1: Pedidos (Sempre tenta incluir se houver dados) ---
    if pedidos_data: body_lines.append(format_pedidos_email(pedidos_data, tipo_decisao)); body_lines.append("")
    else: log.warning("Não há dados de pedidos para incluir no e-mail.")

    # --- Bloco 2: Análise da Decisão (Síntese ou Observações) ---
    added_sintese_obs = False
    if ed_status == "Cabe ED": body_lines.append(f"Trata-se de decisão ({tipo_decisao}) em que se entende cabível Embargos de Declaração:"); body_lines.append(f"Justificativa ED: {justificativa_ed}"); body_lines.append(""); added_sintese_obs = True
    elif sintese_objeto: body_lines.append("SÍNTESE DA DECISÃO / OBJETO DO RECURSO:"); body_lines.append(sintese_objeto); body_lines.append(""); added_sintese_obs = True
    elif obs_decisao: body_lines.append("OBSERVAÇÕES SOBRE A DECISÃO:"); body_lines.append(obs_decisao); body_lines.append(""); added_sintese_obs = True
    # if not added_sintese_obs and not is_homologacao: body_lines.append("") # Evita linha dupla se não houver síntese

    # --- Bloco 3: Detalhes da Execução (Se Homologação) ---
    if is_homologacao:
        body_lines.append(f"Foram homologados os cálculos, determinando o pagamento no prazo de {prazo_pagamento_dias} dias (Fatal: {data_fatal_pagamento_str}), sob pena de penhora.")
        body_lines.append(""); body_lines.append("Valores homologados:")
        if calc_total_homologado > 0: body_lines.append(f"- Valor Total: R$ {calc_total_homologado:.2f}")
        valor_liq_reclamante = calc_principal_liq
        if valor_liq_reclamante > 0: body_lines.append(f"- Principal Líquido: R$ {valor_liq_reclamante:.2f}")
        if calc_inss_emp > 0: body_lines.append(f"- INSS Emp (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
        if calc_fgts > 0: body_lines.append(f"- FGTS: R$ {calc_fgts:.2f} (Conta Vinculada)")
        if calc_hon_suc > 0: body_lines.append(f"- Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
        if calc_hon_per > 0: body_lines.append(f"- Hon. Periciais: R$ {calc_hon_per:.2f}")
        if calc_obs: body_lines.append(f"- Obs Cálculos: {calc_obs}")
        body_lines.append("")

    # --- Bloco 4: Posição/Ação (Depende da Fase e Recurso/916) ---
    if ed_status == "Não cabe ED": # Só avalia Recurso ou Pagamento se não couber ED
        # Cenário A: Recurso Execução Impeditivo (Modelos 3 ou 4)
        if recurso_impeditivo_selecionado:
            recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
            body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Entendemos pela interposição de {recurso_final}:"); body_lines.append(recurso_just if recurso_just else "[JUSTIFICATIVA PENDENTE]"); body_lines.append("")
            if not garantia_necessaria: log.debug("Execução - Modelo 3"); body_lines.append("Considerando a interposição do recurso, as guias de pagamento não foram enviadas."); body_lines.append("Gentileza retornar em 24h se concordam com o posicionamento.")
            else: log.debug("Execução - Modelo 4"); body_lines.append("Recomendamos a garantia do juízo para interposição da medida."); body_lines.append("Requereremos que os valores não sejam transferidos até decisão final."); body_lines.append(""); body_lines.append("Gentileza retornar em 24h se concordam com o posicionamento."); body_lines.append(f"Caso positivo, solicitamos envio dos comprovantes (...) até {data_d_pagamento_str} (Data D-).") # Usa data calculada
            # Lógica de guias se garantia necessária
            if garantia_necessaria and (status_custas == "A Recolher" or status_deposito in ["Garantia do Juízo (Integral)", "A Recolher (Situação Específica)"]):
                 if guias_status == "Guias já elaboradas e salvas": body_lines.append(f"- Guias p/ garantia/pagamento salvas em: {make_hyperlink(local_guias)}")
                 elif guias_status == "Guias pendentes de elaboração": body_lines.append("- Guias p/ garantia/pagamento serão elaboradas.")
            body_lines.append("")

        # Cenário B: Homologação sem Recurso Impeditivo (Modelos 1 ou 2)
        elif is_homologacao:
            if dep_anterior_valor > 0: # Modelo 1
                 log.debug("Execução - Modelo 1"); # ... (Texto Modelo 1 mantido) ...
                 body_lines.append(f"Existem depósitos recursais anteriores aprox. R$ {dep_anterior_valor:.2f}."); body_lines.append("Vamos peticionar pela transferência atualizada."); pagamentos_extras = []
                 if calc_fgts > 0: pagamentos_extras.append("FGTS");
                 if calc_inss_emp > 0: pagamentos_extras.append("INSS Cota Empregado")
                 if pagamentos_extras: body_lines.append(f"Necessário pagamento de: {', '.join(pagamentos_extras)} em guia(s) própria(s)."); body_lines.append(f"Gentileza enviar os comprovantes até {data_d_pagamento_str} (Data D-).")
                 else: body_lines.append("Acompanharemos a transferência.")
                 body_lines.append("")
            else: # Modelo 2 Lógica
                log.debug("Execução - Lógica Modelo 2")
                if opcao_art_916 in ["Oferecer Opção Art. 916", "Cliente Optou por Art. 916"]:
                    log.debug(f"Execução - Modelo 2 - Opção 916: {opcao_art_916}")
                    body_lines.append("Considerando a homologação e ausência de recurso, segue(m) opção(ões) para pagamento:")
                    body_lines.append(""); body_lines.append("**Opção 1: Pagamento Integral**"); body_lines.append(f"- Líquido Reclamante: R$ {valor_liq_reclamante:.2f}"); #...outras verbas...
                    if calc_inss_emp > 0: body_lines.append(f"- INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
                    if calc_fgts > 0: body_lines.append(f"- FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
                    if calc_hon_suc > 0: body_lines.append(f"- Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
                    if calc_hon_per > 0: body_lines.append(f"- Hon. Periciais: R$ {calc_hon_per:.2f}")
                    body_lines.append("- (Verificar status/envio das guias)"); body_lines.append(f"  *Comprovação pagamento integral até {data_d_pagamento_str} (Fatal: {data_fatal_pagamento_str}).*"); body_lines.append("")
                    body_lines.append("**Opção 2: Pagamento Parcelado (Art. 916 CPC)**")
                    if valor_liq_reclamante > 0:
                        valor_entrada_30 = valor_liq_reclamante * 0.30; saldo_remanescente = valor_liq_reclamante * 0.70; num_parcelas = 6; valor_parcela_base = saldo_remanescente / num_parcelas if num_parcelas > 0 else 0
                        body_lines.append(f"- Depósito inicial 30%: R$ {valor_entrada_30:.2f}")
                        body_lines.append("- + Pagamento INTEGRAL e IMEDIATO de:");
                        # <<< CORREÇÃO AQUI: Lista das outras verbas >>>
                        if calc_inss_emp > 0: body_lines.append(f"    - INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
                        if calc_fgts > 0: body_lines.append(f"    - FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
                        if calc_hon_suc > 0: body_lines.append(f"    - Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
                        if calc_hon_per > 0: body_lines.append(f"    - Hon. Periciais: R$ {calc_hon_per:.2f}")
                        # <<< FIM CORREÇÃO >>>
                        body_lines.append(f"- Saldo remanescente (R$ {saldo_remanescente:.2f}) em {num_parcelas} parcelas mensais (+1% a.m. s/ base):")
                        if valor_parcela_base > 0:
                            for n in range(1, num_parcelas + 1): valor_parcela_n = valor_parcela_base * (1 + n * 0.01); body_lines.append(f"    - Parcela {n} aprox.: R$ {valor_parcela_n:.2f}")
                        else: body_lines.append("    - (Erro cálculo parcelas)")
                        body_lines.append("- (Verificar guias p/ entrada e verbas)"); body_lines.append(f"  *Comprovação entrada e verbas até {data_d_pagamento_str} (Fatal: {data_fatal_pagamento_str}).*"); body_lines.append("")
                    else: body_lines.append("  (Não aplicável - Valor líquido zero).")
                    body_lines.append("**Atenção:** Realizar pagamento **APENAS DOS VALORES DA MODALIDADE ESCOLHIDA**.");
                    if opcao_art_916 == "Oferecer Opção Art. 916": body_lines.append(f"*Favor informar a opção desejada até [PRAZO RESPOSTA CLIENTE] e enviar comprovantes até {data_d_pagamento_str}.*")
                    elif opcao_art_916 == "Cliente Optou por Art. 916": body_lines.append(f"*Cliente optou pelo parcelamento. Favor enviar comprovantes da entrada e verbas acessórias até {data_d_pagamento_str}.*")
                else: # Apenas Pagamento Integral
                     log.debug("Execução - Modelo 2 - Pagamento Integral Apenas")
                     body_lines.append("PAGAMENTO NECESSÁRIO (Integral):"); body_lines.append(f"- Líquido Reclamante: R$ {valor_liq_reclamante:.2f}"); # ... detalhar outras verbas ...
                     body_lines.append(f"  *Comprovação do pagamento integral até {data_d_pagamento_str} (Prazo Fatal: {data_fatal_pagamento_str}).*"); body_lines.append("")

        # Cenário C: Fase de Conhecimento ou Outra Decisão de Execução com Recurso
        elif not is_homologacao:
            recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
            body_lines.append("POSIÇÃO DO ESCRITÓRIO:")
            if recurso_rec == "Não Interpor Recurso": body_lines.append(f"Não recomendamos a interposição de recurso."); log.debug("Posição: Não Interpor.")
            else: body_lines.append(f"Recomendamos a interposição de {recurso_final}."); log.debug(f"Posição: Recorrer com {recurso_final}")
            if recurso_just: body_lines.append(f"Justificativa/Objeto: {recurso_just}")
            body_lines.append("")
            precisa_recolher_custas = status_custas == "A Recolher"; precisa_recolher_deposito = status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            if precisa_recolher_custas or precisa_recolher_deposito:
                body_lines.append("PAGAMENTOS NECESSÁRIOS PARA RECORRER:")
                if precisa_recolher_custas: body_lines.append(f"- Custas Processuais: R$ {valor_custas:.2f}.")
                if precisa_recolher_deposito: body_lines.append(f"- Depósito Recursal/Garantia: R$ {valor_deposito:.2f}.")
                if guias_status == "Guias já elaboradas e salvas": body_lines.append(f"- Guias salvas em: {make_hyperlink(local_guias)}")
                elif guias_status == "Guias pendentes de elaboração": body_lines.append("- Guias pendentes de elaboração.")
                body_lines.append("")
            else:
                info_pagamento = []
                if status_custas not in ["A Recolher", "-- Selecione --"]: info_pagamento.append(f"Custas Processuais: {status_custas}.")
                if status_deposito not in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)", "-- Selecione --"]: info_pagamento.append(f"Depósito Recursal/Garantia: {status_deposito}.")
                if info_pagamento: body_lines.extend(info_pagamento); body_lines.append("")

    # --- Bloco 5: Prazos e Call to Action Final ---
    if prazos:
        body_lines.append("PRAZOS RELEVANTES:"); prazo_principal = None; #... (lógica encontrar prazo_acao_imediata) ...
        prazo_acao_imediata = ""; # Reset
        if ed_status == "Cabe ED": prazo_acao_imediata = "Embargos de Declaração"
        elif ed_status == "Não cabe ED" and recurso_rec and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --", "Outro"]: prazo_acao_imediata = recurso_rec
        elif ed_status == "Não cabe ED" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Verificar Recurso Contrário"
        elif fase == "Execução" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Pagamento"

        for p_dict in prazos: # Formata prazos e encontra o principal
             try: p = Prazo(**p_dict); desc = p.descricao; d_fatal_obj = datetime.strptime(p.data_fatal, '%Y-%m-%d').date(); d_d_obj = datetime.strptime(p.data_d, '%Y-%m-%d').date(); d_str = f"(D-: {d_d_obj.strftime('%d/%m/%Y')}, Fatal: {d_fatal_obj.strftime('%d/%m/%Y')})"; body_lines.append(f"- {desc} {d_str}")
             except Exception as e: body_lines.append(f"- Erro ao formatar prazo: {p_dict} - {e}"); continue # Pula para o próximo
             # Lógica para identificar prazo principal (pode precisar de refinamento)
             if prazo_acao_imediata and (prazo_acao_imediata.lower() in desc.lower() or (prazo_acao_imediata=="Pagamento" and "pagamento" in desc.lower())): prazo_principal = p
        body_lines.append("")

        # Call to Action Final (Revisado)
        if prazo_principal:
            try: # Tenta formatar datas do prazo principal
                 data_d_cta = datetime.strptime(prazo_principal.data_d, '%Y-%m-%d').strftime('%d/%m/%Y'); data_fatal_cta = datetime.strptime(prazo_principal.data_fatal, '%Y-%m-%d').strftime('%d/%m/%Y')
            except ValueError: data_d_cta = "[Data D- Inválida]"; data_fatal_cta = "[Data Fatal Inválida]"

            acao_pagamento_cta = status_custas == "A Recolher" or status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            acao_recurso_ed_cta = ed_status == "Cabe ED" or (ed_status == "Não cabe ED" and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"])

            # Não repete CTA de pagamento se já detalhado em Homologação/916
            if acao_pagamento_cta and not is_homologacao and acao_recurso_ed_cta:
                 body_lines.append(f"Solicitamos envio do(s) comprovante(s) de pagamento até {data_d_cta} (Data D-).")

            # Informa prazo fatal da medida principal (Recurso/ED)
            if acao_recurso_ed_cta:
                 body_lines.append(f"O prazo fatal para a medida ({prazo_principal.descricao}) encerra em {data_fatal_cta}.")
                 # Pede confirmação apenas se for recurso e não for execução com garantia (que já pediu)
                 if ed_status != "Cabe ED" and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"] and not (fase=="Execução" and garantia_necessaria):
                      body_lines.append("*Solicitamos retorno quanto ao interesse na interposição do recurso em 48 horas.*")
            # Informa prazo de acompanhamento
            elif recurso_rec == "Não Interpor Recurso" and not is_homologacao: # Se não for Homologação (que já tem CTA específico)
                 body_lines.append(f"Acompanharemos até {data_fatal_cta} para verificar eventual recurso da parte contrária.")

            body_lines.append("") # Garante linha em branco final
        else:
             log.warning("Não foi possível identificar o prazo principal para o Call to Action.")


    # --- Bloco 6: Observações Finais e Assinatura ---
    if obs_finais: body_lines.append("OBSERVAÇÕES FINAIS:"); body_lines.append(obs_finais); body_lines.append("")
    body_lines.append("Qualquer esclarecimento, favor entrar em contato com o escritório."); body_lines.append("")
    body_lines.append("Atenciosamente,"); body_lines.append(""); body_lines.append("[NOME ADVOGADO(A)]")

    log.info("Geração do corpo do e-mail finalizada.")
    return subject, "\n".join(body_lines)

# ========= FIM: Funções Auxiliares =========

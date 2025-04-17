# -*- coding: utf-8 -*-
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
try:
    from parser import PedidoData
except ImportError:
    @dataclass
    class PedidoData: Objetos: str = ""; Situação: str = "N/A"; Res1: str = "N/A"; Res2: str = "N/A"; ResSup: str = "N/A"

import logging
log = logging.getLogger(__name__)

# --- Dataclass Prazo ---
@dataclass
class Prazo:
    descricao: str; data_d: str; data_fatal: str; obs: str = ""

# --- Função para Hiperlink ---
def make_hyperlink(path: str) -> str:
    path_cleaned = path.strip()
    if path_cleaned and (path_cleaned.lower().startswith("http://") or path_cleaned.lower().startswith("https://")): return f"[{path_cleaned}]({path_cleaned})"
    return path_cleaned

# --- Função para formatar prazos ---
def format_prazos(prazos_list: List[Dict[str, Any]]) -> str:
    # ... (Implementação mantida) ...
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

# --- Função para formatar pedidos para Email ---
def format_pedidos_email(pedidos_data: List[PedidoData], tipo_decisao: str) -> str:
    # ... (Implementação mantida) ...
    if not pedidos_data: return "Nenhuma informação de pedido disponível."
    log.debug(f"Formatando {len(pedidos_data)} pedidos para email (Tipo Decisão: {tipo_decisao})")
    linhas_email = []; tipo_lower = tipo_decisao.lower() if tipo_decisao else ""
    if tipo_lower.startswith("sentença"):
        procedentes = []; improcedentes = []; parciais = []; outros = []
        for item in pedidos_data:
            res1 = item.Res1.strip().lower(); objeto = item.Objetos
            if "parcialmente procedente" in res1: parciais.append(f"- {objeto} (Parcialmente Procedente)")
            elif "procedente" in res1: procedentes.append(f"- {objeto}")
            elif "improcedente" in res1: improcedentes.append(f"- {objeto}")
            else: situacao = item.Situação.strip(); outros.append(f"- {objeto} (Situação: {situacao}, Res1: {item.Res1})") if situacao else outros.append(f"- {objeto} (Res1: {item.Res1})")
        if procedentes or parciais: linhas_email.append("Procedentes:"); linhas_email.extend(procedentes); linhas_email.extend(parciais); linhas_email.append("")
        if improcedentes: linhas_email.append("Improcedentes:"); linhas_email.extend(improcedentes); linhas_email.append("")
        if outros: linhas_email.append("Outros Status/Pedidos:"); linhas_email.extend(outros); linhas_email.append("")
    else:
        linhas_email.append("SÍNTESE DOS PEDIDOS / SITUAÇÃO:")
        show_res1 = True; show_res2 = False; show_resSup = False
        if tipo_lower.startswith("acórdão (trt)"): show_res2 = True
        elif tipo_lower.startswith("acórdão (tst"): show_res2 = True; show_resSup = True
        elif tipo_lower.startswith(("decisão monocrática", "despacho denegatório", "homologação de cálculos")): show_res2 = True; show_resSup = True
        header_parts = ["Objeto".ljust(40), "Situação".ljust(15)]; widths = [40, 15]
        if show_res1: header_parts.append("Res. 1ª".ljust(15)); widths.append(15)
        if show_res2: header_parts.append("Res. 2ª".ljust(15)); widths.append(15)
        if show_resSup: header_parts.append("Res. Sup.".ljust(15)); widths.append(15)
        linhas_email.append(" ".join(header_parts)); linhas_email.append("-" * (sum(widths) + len(widths) -1 ))
        for item in pedidos_data:
            data_parts = []; data_parts.append(item.Objetos[:39].ljust(40)); data_parts.append(item.Situação[:14].ljust(15))
            def is_relevant_email(res_value): return res_value and res_value.lower() not in ["aguardando julgamento", "n/a", "", "não houve recurso"]
            if show_res1: data_parts.append(item.Res1[:14].ljust(15) if is_relevant_email(item.Res1) else "-".ljust(15))
            if show_res2: data_parts.append(item.Res2[:14].ljust(15) if is_relevant_email(item.Res2) else "-".ljust(15))
            if show_resSup: data_parts.append(item.ResSup[:14].ljust(15) if is_relevant_email(item.ResSup) else "-".ljust(15))
            linhas_email.append(" ".join(data_parts))
    if not linhas_email: return "Não foi possível formatar a lista de pedidos."
    return "\n".join(linhas_email)


# --- Função para Gerar Corpo e Assunto do Email (Com Cálculo 916 e Prazo Pagamento) ---
def generate_email_body(**kwargs) -> tuple:
    log.info("Gerando corpo do e-mail...")
    # Extrai dados (incluindo novos campos)
    fase = kwargs.get("fase_processual"); tipo_decisao = kwargs.get("tipo_decisao", ""); data_ciencia_str = kwargs.get("data_ciencia").strftime('%d/%m/%Y') if kwargs.get("data_ciencia") else "[DATA CIÊNCIA]"; resultado = kwargs.get("resultado_sentenca"); valor_condenacao = kwargs.get("valor_condenacao_execucao", 0.0); obs_decisao = kwargs.get("obs_sentenca"); sintese_objeto = kwargs.get("sintese_objeto_recurso", ""); pedidos_data = kwargs.get("pedidos_data", []); ed_status = kwargs.get("ed_status"); justificativa_ed = kwargs.get("justificativa_ed"); recurso_rec = kwargs.get("recurso_selecionado"); recurso_outro = kwargs.get("recurso_outro_especificar"); recurso_just = kwargs.get("recurso_justificativa"); garantia_necessaria = kwargs.get("garantia_necessaria", False); status_custas = kwargs.get("status_custas"); valor_custas = kwargs.get("valor_custas", 0.0); status_deposito = kwargs.get("status_deposito"); valor_deposito = kwargs.get("valor_deposito_input", 0.0); guias_status = kwargs.get("guias_status"); local_guias = kwargs.get("local_guias"); prazos = kwargs.get("prazos", []); obs_finais = kwargs.get("obs_finais"); calc_principal_liq = kwargs.get("calc_principal_liq", 0.0); calc_inss_emp = kwargs.get("calc_inss_emp", 0.0); calc_fgts = kwargs.get("calc_fgts", 0.0); calc_hon_suc = kwargs.get("calc_hon_suc", 0.0); calc_hon_per = kwargs.get("calc_hon_per", 0.0); calc_total_homologado = kwargs.get("calc_total_homologado", 0.0); calc_obs = kwargs.get("calc_obs",""); dep_anterior_valor = kwargs.get("dep_anterior_valor", 0.0); dep_anterior_detalhes = kwargs.get("dep_anterior_detalhes","")
    # <<< NOVOS VALORES >>>
    prazo_pagamento_dias = kwargs.get("prazo_pagamento_dias", 15) # Pega do state, default 15
    opcao_art_916 = kwargs.get("opcao_art_916", "Não oferecer/Não aplicável") # Pega do state

    subject = f"TRABALHISTA: {tipo_decisao.split('(')[0].strip()} ({fase}) - [ADVERSO] X [CLIENTE] - Proc [Nº PROCESSO]"
    body_lines = []; body_lines.append("Prezados, bom dia!"); body_lines.append("")
    body_lines.append(f"Local: [LOCAL]"); body_lines.append(f"Processo nº: [Nº PROCESSO]")
    body_lines.append(f"Cliente: [CLIENTE]"); body_lines.append(f"Adverso: [ADVERSO]"); body_lines.append("")
    body_lines.append(f"Pelo presente, informamos a decisão ({tipo_decisao} / {fase}) publicada/disponibilizada em {data_ciencia_str}.")
    body_lines.append("")

    is_homologacao = fase == "Execução" and tipo_decisao and "Homologação de Cálculos" in tipo_decisao

    if is_homologacao:
        # <<< USA prazo_pagamento_dias >>>
        body_lines.append(f"Foram homologados os cálculos, determinando o pagamento no prazo de {prazo_pagamento_dias} dias, sob pena de penhora.")
        body_lines.append(""); body_lines.append("Seguem os valores homologados:")
        # (Restante da lógica de exibição dos cálculos mantida)
        if calc_total_homologado > 0: body_lines.append(f"- Valor Total da Execução: R$ {calc_total_homologado:.2f}")
        valor_liq_reclamante = calc_principal_liq
        if valor_liq_reclamante > 0: body_lines.append(f"- Principal Líquido (+ Juros se incluso): R$ {valor_liq_reclamante:.2f}")
        if calc_inss_emp > 0: body_lines.append(f"- INSS Cota Empregado (Base): R$ {calc_inss_emp:.2f} (Recolher em guia própria via e-social)")
        if calc_fgts > 0: body_lines.append(f"- FGTS (+Taxa se inclusa): R$ {calc_fgts:.2f} (Depositar em conta vinculada)")
        if calc_hon_suc > 0: body_lines.append(f"- Honorários Advocatícios Sucumbência: R$ {calc_hon_suc:.2f}")
        if calc_hon_per > 0: body_lines.append(f"- Honorários Periciais: R$ {calc_hon_per:.2f}")
        if calc_obs: body_lines.append(f"- Observações sobre Cálculos: {calc_obs}")
        body_lines.append("")

        if dep_anterior_valor > 0: # Modelo 1
            # ... (Lógica Modelo 1 mantida) ...
            body_lines.append(f"Existem depósitos recursais anteriores totalizando aprox. R$ {dep_anterior_valor:.2f}.")
            if dep_anterior_detalhes: body_lines.append(f"  Detalhes: {dep_anterior_detalhes}")
            body_lines.append("Vamos peticionar requerendo a transferência dos depósitos atualizados para abatimento.")
            pagamentos_extras = []
            if calc_fgts > 0: pagamentos_extras.append("FGTS")
            if calc_inss_emp > 0: pagamentos_extras.append("INSS Cota Empregado")
            if pagamentos_extras:
                 body_lines.append(f"Ainda é necessário o pagamento de: {', '.join(pagamentos_extras)} em guia(s) própria(s).")
                 body_lines.append("Na petição informaremos que estas guias foram pagas.")
                 body_lines.append("Gentileza enviar os comprovantes até [DATA D- PAGAMENTO].")
            else: body_lines.append("Acompanharemos a transferência e informaremos sobre saldo residual.")
            body_lines.append("")

        # <<< CONDIÇÃO AJUSTADA PARA INCLUIR opcao_art_916 >>>
        elif recurso_rec == "Não Interpor Recurso" and opcao_art_916 != "Não oferecer/Não aplicável": # Modelo 2 (Oferecendo ou Confirmando 916)
            body_lines.append("Não havendo intenção de recurso, seguem opções para pagamento:")
            body_lines.append("")
            body_lines.append("**Opção 1: Pagamento Integral**")
            body_lines.append(f"- Líquido Reclamante: R$ {valor_liq_reclamante:.2f}")
            # ... (detalhes das outras verbas a pagar integralmente) ...
            if calc_inss_emp > 0: body_lines.append(f"- INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
            if calc_fgts > 0: body_lines.append(f"- FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
            if calc_hon_suc > 0: body_lines.append(f"- Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
            if calc_hon_per > 0: body_lines.append(f"- Hon. Periciais: R$ {calc_hon_per:.2f}")
            body_lines.append("- (Verificar envio/status das guias correspondentes)")
            body_lines.append(f"  *Comprovação do pagamento integral até [DATA D- PAGAMENTO INTEGRAL] (Prazo fatal: [DATA FATAL PAGAMENTO INTEGRAL]).*"); body_lines.append("")

            body_lines.append("**Opção 2: Pagamento Parcelado (Art. 916 CPC)**")
            if valor_liq_reclamante > 0:
                valor_entrada_30 = valor_liq_reclamante * 0.30
                saldo_remanescente = valor_liq_reclamante * 0.70
                num_parcelas = 6
                valor_parcela_base = saldo_remanescente / num_parcelas if num_parcelas > 0 else 0
                body_lines.append(f"- Depósito inicial de 30% do Líquido Reclamante: R$ {valor_entrada_30:.2f}")
                body_lines.append("- + Pagamento INTEGRAL de:")
                if calc_inss_emp > 0: body_lines.append(f"    - INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
                # ... (outras verbas acessórias) ...
                if calc_fgts > 0: body_lines.append(f"    - FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
                if calc_hon_suc > 0: body_lines.append(f"    - Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
                if calc_hon_per > 0: body_lines.append(f"    - Hon. Periciais: R$ {calc_hon_per:.2f}")
                body_lines.append(f"- Saldo remanescente (R$ {saldo_remanescente:.2f}) em {num_parcelas} parcelas mensais (+1% a.m. sobre valor base):")
                if valor_parcela_base > 0:
                    for n in range(1, num_parcelas + 1):
                        valor_parcela_n = valor_parcela_base * (1 + n * 0.01)
                        body_lines.append(f"    - Parcela {n} aprox.: R$ {valor_parcela_n:.2f}") # Deixa claro que é aprox. devido a arredondamentos/juros exatos
                else: body_lines.append("    - (Erro no cálculo das parcelas)")
                body_lines.append("- (Verificar envio/status das guias p/ entrada e outras verbas)")
                body_lines.append(f"  *Comprovação pagamento da entrada e demais verbas até [DATA D- PAGAMENTO ENTRADA] (Prazo fatal: [DATA FATAL PAGAMENTO ENTRADA]).*"); body_lines.append("")
            else: body_lines.append("  (Não aplicável - Valor líquido zero).")

            # Ajusta chamada de ação se for apenas para oferecer ou se cliente já optou
            if opcao_art_916 == "Oferecer Opção Art. 916":
                 body_lines.append("*Favor informar a opção de pagamento desejada (Integral ou Parcelada) e enviar comprovantes até [DATA D- PAGAMENTO].*")
            elif opcao_art_916 == "Cliente Optou por Art. 916":
                 body_lines.append("*Cliente optou pelo parcelamento. Favor enviar comprovantes da entrada e demais verbas até [DATA D- PAGAMENTO].*")

        # Outros Cenários (Modelo 3 e 4 - lógica mantida)
        elif recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"] and not garantia_necessaria: # Modelo 3
             # ... (Texto Modelo 3) ...
             recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
             body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Entendemos pela oposição de {recurso_final}, pelos seguintes motivos:")
             body_lines.append(recurso_just if recurso_just else "[JUSTIFICATIVA PENDENTE]"); body_lines.append("")
             body_lines.append("Considerando a interposição da medida recursal, as guias de pagamento não foram enviadas."); body_lines.append("Gentileza retornar em 24 horas se concordam com o posicionamento.")
        elif recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"] and garantia_necessaria: # Modelo 4
             # ... (Texto Modelo 4) ...
             recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
             body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Entendemos pela oposição de {recurso_final}, pelos seguintes motivos:"); body_lines.append(recurso_just if recurso_just else "[JUSTIFICATIVA PENDENTE]"); body_lines.append("")
             body_lines.append("Recomendamos a garantia do juízo para a interposição da medida."); body_lines.append("Vamos requerer que os valores não sejam transferidos ao adverso até a decisão final."); body_lines.append("")
             body_lines.append("Gentileza retornar em 24 horas se concordam com o posicionamento."); body_lines.append("Caso positivo, solicitamos o envio dos comprovantes de pagamento (...) até [DATA D- PAGAMENTO GARANTIA].")
             if status_custas == "A Recolher" or status_deposito in ["Garantia do Juízo (Integral)", "A Recolher (Situação Específica)"]: # Ajustado status depósito
                 if guias_status == "Guias já elaboradas e salvas": body_lines.append(f"- Guias p/ garantia/pagamento salvas em: {make_hyperlink(local_guias)}")
                 elif guias_status == "Guias pendentes de elaboração": body_lines.append("- Guias p/ garantia/pagamento serão elaboradas.")

    # --- Lógica para Outras Decisões (Conhecimento ou outras de Execução) ---
    else:
        # (Lógica mantida da versão anterior)
        if pedidos_data: body_lines.append(format_pedidos_email(pedidos_data, tipo_decisao)); body_lines.append("")
        # ... (Síntese, ED, Recurso, Custas, Depósito, Guias...)

    # --- Seção Comum Final (Prazos, Call to Action, Obs Finais) ---
    # (Lógica mantida da versão anterior)
    # ...

    # --- Assinatura Final ---
    body_lines.append("Qualquer esclarecimento, favor entrar em contato com o escritório."); body_lines.append("")
    body_lines.append("Atenciosamente,"); body_lines.append(""); body_lines.append("[NOME ADVOGADO(A)]")

    return subject, "\n".join(body_lines)


# ========= FIM: Funções Auxiliares =========

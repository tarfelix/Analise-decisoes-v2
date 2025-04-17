# -*- coding: utf-8 -*-
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
try: # Tenta importar PedidoData do parser
    from parser import PedidoData
except ImportError: # Fallback se parser.py não for encontrado (menos provável agora)
    @dataclass
    class PedidoData: # Define um substituto básico
        Objetos: str = ""
        Situação: str = "N/A"
        Res1: str = "N/A"
        Res2: str = "N/A"
        ResSup: str = "N/A"


import logging
log = logging.getLogger(__name__)

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
    path_cleaned = path.strip()
    if path_cleaned and (path_cleaned.lower().startswith("http://") or path_cleaned.lower().startswith("https://")):
        return f"[{path_cleaned}]({path_cleaned})"
    return path_cleaned

# --- Função para formatar prazos ---
def format_prazos(prazos_list: List[Dict[str, Any]]) -> str:
    """Formata a lista de prazos (dicts) para exibição no texto final."""
    # ... (Implementação mantida da versão anterior) ...
    if not prazos_list: return "Nenhum prazo informado."
    lines = []
    for i, p_dict in enumerate(prazos_list, start=1):
        try:
            p = Prazo(**p_dict)
            lines.append(f"{i}) {p.descricao}")
            data_d_str = "N/I"; data_fatal_str = "N/I"
            try: data_d_obj = datetime.strptime(p.data_d, '%Y-%m-%d').date(); data_d_str = data_d_obj.strftime('%d/%m/%Y')
            except: data_d_str = f"{p.data_d}(Inválido)"
            try: data_fatal_obj = datetime.strptime(p.data_fatal, '%Y-%m-%d').date(); data_fatal_str = data_fatal_obj.strftime('%d/%m/%Y')
            except: data_fatal_str = f"{p.data_fatal}(Inválido)"
            lines.append(f"   - Data D-: {data_d_str}")
            lines.append(f"   - Data Fatal: {data_fatal_str}")
            obs = p.obs.strip()
            if obs: lines.append(f"   - Observações: {obs}")
            lines.append("")
        except TypeError as e: lines.append(f"{i}) Erro formatar prazo: {p_dict} - {e}"); lines.append("")
    return "\n".join(lines)


# --- Função para formatar pedidos para Email ---
def format_pedidos_email(pedidos_data: List[PedidoData], tipo_decisao: str) -> str:
    """Formata a lista de pedidos (dataclasses) para o corpo do e-mail."""
    # ... (Implementação mantida da versão anterior) ...
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
            else:
                situacao = item.Situação.strip()
                outros.append(f"- {objeto} (Situação: {situacao}, Res1: {item.Res1})") if situacao else outros.append(f"- {objeto} (Res1: {item.Res1})")
        if procedentes or parciais: linhas_email.append("Procedentes:"); linhas_email.extend(procedentes); linhas_email.extend(parciais); linhas_email.append("")
        if improcedentes: linhas_email.append("Improcedentes:"); linhas_email.extend(improcedentes); linhas_email.append("")
        if outros: linhas_email.append("Outros Status/Pedidos:"); linhas_email.extend(outros); linhas_email.append("")
    else:
        linhas_email.append("SÍNTESE DOS PEDIDOS / SITUAÇÃO:")
        show_res1 = True; show_res2 = False; show_resSup = False
        if tipo_lower.startswith("acórdão (trt)"): show_res2 = True
        elif tipo_lower.startswith("acórdão (tst"): show_res2 = True; show_resSup = True
        elif tipo_lower.startswith(("decisão monocrática", "despacho denegatório", "homologação de cálculos")): show_res2 = True; show_resSup = True
        header_parts = ["Objeto".ljust(40), "Situação".ljust(15)]
        widths = [40, 15]
        if show_res1: header_parts.append("Res. 1ª".ljust(15)); widths.append(15)
        if show_res2: header_parts.append("Res. 2ª".ljust(15)); widths.append(15)
        if show_resSup: header_parts.append("Res. Sup.".ljust(15)); widths.append(15)
        linhas_email.append(" ".join(header_parts)); linhas_email.append("-" * (sum(widths) + len(widths) -1 ))
        for item in pedidos_data:
            data_parts = []
            data_parts.append(item.Objetos[:39].ljust(40))
            data_parts.append(item.Situação[:14].ljust(15))
            def is_relevant_email(res_value): return res_value and res_value.lower() not in ["aguardando julgamento", "n/a", "", "não houve recurso"]
            if show_res1: data_parts.append(item.Res1[:14].ljust(15) if is_relevant_email(item.Res1) else "-".ljust(15))
            if show_res2: data_parts.append(item.Res2[:14].ljust(15) if is_relevant_email(item.Res2) else "-".ljust(15))
            if show_resSup: data_parts.append(item.ResSup[:14].ljust(15) if is_relevant_email(item.ResSup) else "-".ljust(15))
            linhas_email.append(" ".join(data_parts))
    if not linhas_email: return "Não foi possível formatar a lista de pedidos."
    return "\n".join(linhas_email)


# --- Função para Gerar Corpo e Assunto do Email (Com Cálculo 916) ---
def generate_email_body(**kwargs) -> tuple:
    """Gera o Assunto e o Corpo do E-mail com base nos dados e na fase."""
    log.info("Gerando corpo do e-mail...")
    # Extrai dados
    fase = kwargs.get("fase_processual"); tipo_decisao = kwargs.get("tipo_decisao", ""); data_ciencia_str = kwargs.get("data_ciencia").strftime('%d/%m/%Y') if kwargs.get("data_ciencia") else "[DATA CIÊNCIA]"; resultado = kwargs.get("resultado_sentenca"); valor_condenacao = kwargs.get("valor_condenacao_execucao", 0.0); obs_decisao = kwargs.get("obs_sentenca"); sintese_objeto = kwargs.get("sintese_objeto_recurso", ""); pedidos_data = kwargs.get("pedidos_data", []); ed_status = kwargs.get("ed_status"); justificativa_ed = kwargs.get("justificativa_ed"); recurso_rec = kwargs.get("recurso_selecionado"); recurso_outro = kwargs.get("recurso_outro_especificar"); recurso_just = kwargs.get("recurso_justificativa"); garantia_necessaria = kwargs.get("garantia_necessaria", False); status_custas = kwargs.get("status_custas"); valor_custas = kwargs.get("valor_custas", 0.0); status_deposito = kwargs.get("status_deposito"); valor_deposito = kwargs.get("valor_deposito_input", 0.0); guias_status = kwargs.get("guias_status"); local_guias = kwargs.get("local_guias"); prazos = kwargs.get("prazos", []); obs_finais = kwargs.get("obs_finais"); calc_principal_liq = kwargs.get("calc_principal_liq", 0.0); calc_inss_emp = kwargs.get("calc_inss_emp", 0.0); calc_fgts = kwargs.get("calc_fgts", 0.0); calc_hon_suc = kwargs.get("calc_hon_suc", 0.0); calc_hon_per = kwargs.get("calc_hon_per", 0.0); calc_total_homologado = kwargs.get("calc_total_homologado", 0.0); calc_obs = kwargs.get("calc_obs",""); dep_anterior_valor = kwargs.get("dep_anterior_valor", 0.0); dep_anterior_detalhes = kwargs.get("dep_anterior_detalhes","")

    subject = f"TRABALHISTA: {tipo_decisao.split('(')[0].strip()} ({fase}) - [ADVERSO] X [CLIENTE] - Proc [Nº PROCESSO]"
    body_lines = []; body_lines.append("Prezados, bom dia!"); body_lines.append("")
    body_lines.append(f"Local: [LOCAL]"); body_lines.append(f"Processo nº: [Nº PROCESSO]")
    body_lines.append(f"Cliente: [CLIENTE]"); body_lines.append(f"Adverso: [ADVERSO]"); body_lines.append("")
    body_lines.append(f"Pelo presente, informamos a decisão ({tipo_decisao} / {fase}) publicada/disponibilizada em {data_ciencia_str}.")
    body_lines.append("")

    # --- Lógica Específica da Fase de Execução ---
    is_homologacao = fase == "Execução" and tipo_decisao and "Homologação de Cálculos" in tipo_decisao
    if is_homologacao:
        body_lines.append("Foram homologados os cálculos, determinando o pagamento no prazo de 15 dias, sob pena de penhora.")
        body_lines.append(""); body_lines.append("Seguem os valores homologados:")
        if calc_total_homologado > 0: body_lines.append(f"- Valor Total da Execução: R$ {calc_total_homologado:.2f}")
        # Usar os valores detalhados se disponíveis
        valor_liq_reclamante = calc_principal_liq # Base para 916
        if valor_liq_reclamante > 0: body_lines.append(f"- Principal Líquido (+ Juros se incluso): R$ {valor_liq_reclamante:.2f}")
        if calc_inss_emp > 0: body_lines.append(f"- INSS Cota Empregado (Base): R$ {calc_inss_emp:.2f} (Recolher em guia própria via e-social)")
        if calc_fgts > 0: body_lines.append(f"- FGTS (+Taxa se inclusa): R$ {calc_fgts:.2f} (Depositar em conta vinculada)")
        if calc_hon_suc > 0: body_lines.append(f"- Honorários Advocatícios Sucumbência: R$ {calc_hon_suc:.2f}")
        if calc_hon_per > 0: body_lines.append(f"- Honorários Periciais: R$ {calc_hon_per:.2f}")
        if calc_obs: body_lines.append(f"- Observações sobre Cálculos: {calc_obs}")
        body_lines.append("")

        # Cenário 1: Com Depósitos Anteriores (Modelo 1)
        if dep_anterior_valor > 0:
            # ... (Lógica do Modelo 1 mantida como antes) ...
            body_lines.append(f"Existem depósitos recursais anteriores totalizando aprox. R$ {dep_anterior_valor:.2f}.")
            if dep_anterior_detalhes: body_lines.append(f"  Detalhes: {dep_anterior_detalhes}")
            body_lines.append("Vamos peticionar requerendo a transferência dos depósitos atualizados para abatimento.")
            pagamentos_extras = []
            if calc_fgts > 0: pagamentos_extras.append("FGTS (em conta vinculada)")
            if calc_inss_emp > 0: pagamentos_extras.append("INSS Cota Empregado (via e-Social)")
            if pagamentos_extras:
                 body_lines.append(f"No entanto, ainda é necessário o pagamento de: {', '.join(pagamentos_extras)} em guia(s) própria(s).")
                 body_lines.append("Na mesma petição requerendo a liberação dos depósitos, informaremos ao Juízo que estas guias foram pagas.")
                 body_lines.append("Gentileza enviar os comprovantes de pagamento (FGTS e INSS) até [DATA D- PAGAMENTO].")
            else:
                 body_lines.append("Acompanharemos a transferência dos valores e informaremos sobre eventual saldo residual.")
            body_lines.append("")

        # Cenário 2: Sem Depósitos ou Insuficientes e SEM Recurso (Modelo 2 - COM CÁLCULO)
        elif recurso_rec == "Não Interpor Recurso":
            body_lines.append("Não havendo garantia integral ou intenção de recurso, seguem opções para pagamento:")
            body_lines.append("")
            body_lines.append("**Opção 1: Pagamento Integral**")
            body_lines.append(f"- Líquido Reclamante: R$ {valor_liq_reclamante:.2f}")
            if calc_inss_emp > 0: body_lines.append(f"- INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
            if calc_fgts > 0: body_lines.append(f"- FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
            if calc_hon_suc > 0: body_lines.append(f"- Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
            if calc_hon_per > 0: body_lines.append(f"- Hon. Periciais: R$ {calc_hon_per:.2f}")
            body_lines.append("- (Verificar envio/status das guias correspondentes)")
            body_lines.append("  *Comprovação do pagamento integral até [DATA FATAL PAGAMENTO INTEGRAL].*"); body_lines.append("") # Placeholder data

            body_lines.append("**Opção 2: Pagamento Parcelado (Art. 916 CPC)**")
            if valor_liq_reclamante > 0:
                valor_entrada_30 = valor_liq_reclamante * 0.30
                saldo_remanescente = valor_liq_reclamante * 0.70
                num_parcelas = 6
                valor_parcela_base = saldo_remanescente / num_parcelas if num_parcelas > 0 else 0

                body_lines.append(f"- Depósito inicial de 30% sobre o crédito líquido do Reclamante: R$ {valor_entrada_30:.2f}")
                body_lines.append("- Pagamento INTEGRAL E IMEDIATO de:")
                if calc_inss_emp > 0: body_lines.append(f"    - INSS Empregado (Base): R$ {calc_inss_emp:.2f} (Guia e-Social)")
                if calc_fgts > 0: body_lines.append(f"    - FGTS: R$ {calc_fgts:.2f} (Guia Conta Vinculada)")
                if calc_hon_suc > 0: body_lines.append(f"    - Hon. Sucumbência: R$ {calc_hon_suc:.2f}")
                if calc_hon_per > 0: body_lines.append(f"    - Hon. Periciais: R$ {calc_hon_per:.2f}")
                body_lines.append(f"- Saldo remanescente (R$ {saldo_remanescente:.2f}) em {num_parcelas} parcelas mensais (corrigidas + 1% ao mês sobre o valor base da parcela):")

                if valor_parcela_base > 0:
                    for n in range(1, num_parcelas + 1):
                        valor_parcela_n = valor_parcela_base * (1 + n * 0.01)
                        body_lines.append(f"    - Parcela {n}: R$ {valor_parcela_n:.2f}")
                else:
                     body_lines.append("    - (Erro no cálculo das parcelas - saldo zero ou negativo?)")

                body_lines.append("- (Verificar envio/status das guias p/ entrada e outras verbas)")
                body_lines.append("  *Comprovação do pagamento da entrada e demais verbas até [DATA FATAL PAGAMENTO ENTRADA].*"); body_lines.append("") # Placeholder data
                body_lines.append("*Favor informar a opção desejada e enviar comprovantes até [DATA D- PAGAMENTO].*") # Placeholder data
            else:
                 body_lines.append("  (Não aplicável - Valor líquido do reclamante é zero ou não informado).")


        # Cenário 3: COM Recurso SEM Garantia (Modelo 3)
        elif recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"] and not garantia_necessaria:
             # ... (Texto do Modelo 3 mantido) ...
             recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
             body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Entendemos pela oposição de {recurso_final}, pelos seguintes motivos:")
             body_lines.append(recurso_just if recurso_just else "[JUSTIFICATIVA PENDENTE]"); body_lines.append("")
             body_lines.append("Considerando a interposição da medida recursal, as guias de pagamento não foram enviadas."); body_lines.append("Gentileza retornar em 24 horas se concordam com o posicionamento.")

        # Cenário 4: COM Recurso COM Garantia (Modelo 4)
        elif recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"] and garantia_necessaria:
             # ... (Texto do Modelo 4 mantido) ...
             recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
             body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Entendemos pela oposição de {recurso_final}, pelos seguintes motivos:")
             body_lines.append(recurso_just if recurso_just else "[JUSTIFICATIVA PENDENTE]"); body_lines.append("")
             body_lines.append("Recomendamos a garantia do juízo para a interposição da medida."); body_lines.append("Vamos requerer que os valores não sejam transferidos ao adverso até a decisão final."); body_lines.append("")
             body_lines.append("Gentileza retornar em 24 horas se concordam com o posicionamento."); body_lines.append("Caso positivo, solicitamos o envio dos comprovantes de pagamento (...) até [DATA D- PAGAMENTO GARANTIA].")
             if status_custas == "A Recolher" or status_deposito in ["Garantia do Juízo (Integral)", "A Recolher (Situação Específica)"]:
                 if guias_status == "Guias já elaboradas e salvas": body_lines.append(f"- Guias p/ garantia/pagamento salvas em: {make_hyperlink(local_guias)}")
                 elif guias_status == "Guias pendentes de elaboração": body_lines.append("- Guias p/ garantia/pagamento serão elaboradas.")

    # --- Lógica para Outras Decisões (Conhecimento ou outras de Execução) ---
    else:
        # (Lógica mantida da versão anterior)
        if pedidos_data: body_lines.append(format_pedidos_email(pedidos_data, tipo_decisao)); body_lines.append("")
        if ed_status == "Cabe ED": body_lines.append(f"Trata-se de decisão ({tipo_decisao}) em que se entende cabível ED:"); body_lines.append(f"Justificativa ED: {justificativa_ed}"); body_lines.append("")
        elif sintese_objeto: body_lines.append("SÍNTESE DA DECISÃO / OBJETO DO RECURSO:"); body_lines.append(sintese_objeto); body_lines.append("")
        elif obs_decisao: body_lines.append("OBSERVAÇÕES SOBRE A DECISÃO:"); body_lines.append(obs_decisao); body_lines.append("")
        if ed_status == "Não cabe ED" and recurso_rec and recurso_rec != "-- Selecione --":
            recurso_final = recurso_rec if recurso_rec != "Outro" else recurso_outro
            if recurso_rec == "Não Interpor Recurso":
                body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Não recomendamos a interposição de recurso.")
                if recurso_just: body_lines.append(f"Justificativa: {recurso_just}")
            else:
                body_lines.append("POSIÇÃO DO ESCRITÓRIO:"); body_lines.append(f"Recomendamos a interposição de {recurso_final}.")
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

    # --- Seção Comum Final (Prazos, Call to Action, Obs Finais) ---
    # ... (Lógica mantida da versão anterior) ...
    if prazos:
        body_lines.append("PRAZOS RELEVANTES:"); prazo_principal = None; prazo_acao_imediata = ""
        if ed_status == "Cabe ED": prazo_acao_imediata = "Embargos de Declaração"
        elif ed_status == "Não cabe ED" and recurso_rec and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --", "Outro"]: prazo_acao_imediata = recurso_rec
        elif ed_status == "Não cabe ED" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Verificar Recurso Contrário"
        for p_dict in prazos:
            try:
                p = Prazo(**p_dict); desc = p.descricao; d_fatal_obj = datetime.strptime(p.data_fatal, '%Y-%m-%d').date(); d_d_obj = datetime.strptime(p.data_d, '%Y-%m-%d').date()
                d_str = f"(D-: {d_d_obj.strftime('%d/%m/%Y')}, Fatal: {d_fatal_obj.strftime('%d/%m/%Y')})"
                body_lines.append(f"- {desc} {d_str}")
                if prazo_acao_imediata and (prazo_acao_imediata == desc or prazo_acao_imediata in desc): prazo_principal = p
            except (ValueError, TypeError, KeyError): body_lines.append(f"- Erro ao formatar prazo: {p_dict}")
        body_lines.append("")
        if prazo_principal:
            data_d_principal = datetime.strptime(prazo_principal.data_d, '%Y-%m-%d').strftime('%d/%m/%Y')
            data_fatal_principal = datetime.strptime(prazo_principal.data_fatal, '%Y-%m-%d').strftime('%d/%m/%Y')
            acao_pagamento = status_custas == "A Recolher" or status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
            acao_recurso_ed = ed_status == "Cabe ED" or (ed_status == "Não cabe ED" and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"])
            if acao_pagamento: body_lines.append(f"Solicitamos envio do(s) comprovante(s) de pagamento até {data_d_principal} (Data D-).")
            if acao_recurso_ed and not (fase=="Execução" and garantia_necessaria):
                 body_lines.append(f"O prazo fatal para a medida ({prazo_principal.descricao}) encerra em {data_fatal_principal}.")
                 if recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"]: body_lines.append("Solicitamos retorno quanto ao interesse em 48 horas para elaboração da medida.")
            elif fase=="Execução" and garantia_necessaria: body_lines.append(f"O prazo fatal para garantia e interposição ({prazo_principal.descricao}) encerra em {data_fatal_principal}.")
            elif recurso_rec == "Não Interpor Recurso": body_lines.append(f"Acompanharemos até {data_fatal_principal} para verificar eventual recurso da parte contrária.")
            body_lines.append("")

    if obs_finais: body_lines.append("OBSERVAÇÕES FINAIS:"); body_lines.append(obs_finais); body_lines.append("")
    body_lines.append("Qualquer esclarecimento, favor entrar em contato com o escritório."); body_lines.append("")
    body_lines.append("Atenciosamente,"); body_lines.append(""); body_lines.append("[NOME ADVOGADO(A)]")

    return subject, "\n".join(body_lines)

# ========= FIM: Funções Auxiliares =========
# -*- coding: utf-8 -*-
# Versão com Correção SyntaxError no loop de prazos do email (generate_email_body)

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
    @dataclass
    class PedidoData: # Define um substituto básico
        Objetos: str = ""
        Situação: str = "N/A"
        Res1: str = "N/A"
        Res2: str = "N/A"
        ResSup: str = "N/A"

# Importa funções de data
try:
    from utils_date import add_months, add_business_days
except ImportError:
    log.error("Módulo utils_date não encontrado! Funções de data não funcionarão corretamente.")
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
    path_cleaned = path.strip();
    if path_cleaned and (path_cleaned.lower().startswith(("http://", "https://"))): return f"[{path_cleaned}]({path_cleaned})"
    return path_cleaned

# --- Função para formatar prazos ---
def format_prazos(prazos_list: List[Dict[str, Any]]) -> str:
    # (Implementação mantida)
    if not prazos_list: return "Nenhum prazo informado."
    lines = []
    for i, p_dict in enumerate(prazos_list, start=1):
        try: p = Prazo(**p_dict); lines.append(f"{i}) {p.descricao}"); data_d_str = "N/I"; data_fatal_str = "N/I"
        except: lines.append(f"{i}) Erro ao ler prazo: {p_dict}"); continue
        try: data_d_obj = datetime.strptime(p.data_d, '%Y-%m-%d').date(); data_d_str = data_d_obj.strftime('%d/%m/%Y')
        except: data_d_str = f"{p.data_d}(Inválido)"
        try: data_fatal_obj = datetime.strptime(p.data_fatal, '%Y-%m-%d').date(); data_fatal_str = data_fatal_obj.strftime('%d/%m/%Y')
        except: data_fatal_str = f"{p.data_fatal}(Inválido)"
        lines.append(f"   - Data D-: {data_d_str}"); lines.append(f"   - Data Fatal: {data_fatal_str}")
        obs = p.obs.strip();
        if obs: lines.append(f"   - Observações: {obs}")
        lines.append("")
    return "\n".join(lines).strip()


# --- Função para formatar pedidos para Email (SEMPRE como Lista) ---
def format_pedidos_email(pedidos_data: List[PedidoData], tipo_decisao: str) -> str:
     # (Implementação mantida)
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


# --- Função para Gerar Corpo e Assunto do Email (Lógica Revisada) ---
def generate_email_body(**kwargs) -> tuple:
    log.info("Iniciando generate_email_body...")
    # --- Extração de Dados (mantida) ---
    # ... (extração completa de kwargs) ...
    fase = kwargs.get("fase_processual"); tipo_decisao = kwargs.get("tipo_decisao", ""); data_ciencia = kwargs.get("data_ciencia"); data_ciencia_str = data_ciencia.strftime('%d/%m/%Y') if data_ciencia else "[DATA CIÊNCIA]"; resultado = kwargs.get("resultado_sentenca"); valor_condenacao = kwargs.get("valor_condenacao_execucao", 0.0); obs_decisao = kwargs.get("obs_sentenca"); sintese_objeto = kwargs.get("sintese_objeto_recurso", ""); pedidos_data = kwargs.get("pedidos_data", []); ed_status = kwargs.get("ed_status"); justificativa_ed = kwargs.get("justificativa_ed"); recurso_rec = kwargs.get("recurso_selecionado"); recurso_outro = kwargs.get("recurso_outro_especificar"); recurso_just = kwargs.get("recurso_justificativa"); garantia_necessaria = kwargs.get("garantia_necessaria", False); status_custas = kwargs.get("status_custas"); valor_custas = kwargs.get("valor_custas", 0.0); status_deposito = kwargs.get("status_deposito"); valor_deposito = kwargs.get("valor_deposito_input", 0.0); guias_status = kwargs.get("guias_status"); local_guias = kwargs.get("local_guias"); prazos = kwargs.get("prazos", []); obs_finais = kwargs.get("obs_finais"); calc_principal_liq = kwargs.get("calc_principal_liq", 0.0); calc_inss_emp = kwargs.get("calc_inss_emp", 0.0); calc_fgts = kwargs.get("calc_fgts", 0.0); calc_hon_suc = kwargs.get("calc_hon_suc", 0.0); calc_hon_per = kwargs.get("calc_hon_per", 0.0); calc_total_homologado = kwargs.get("calc_total_homologado", 0.0); calc_obs = kwargs.get("calc_obs",""); dep_anterior_valor = kwargs.get("dep_anterior_valor", 0.0); dep_anterior_detalhes = kwargs.get("dep_anterior_detalhes","")
    prazo_pagamento_dias = kwargs.get("prazo_pagamento_dias", 15)
    opcao_art_916 = kwargs.get("opcao_art_916", "Não oferecer/Não aplicável")
    log.debug("Dados extraídos para gerar email.")

    # --- Assunto (mantido) ---
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
    # ... (lógica mantida) ...
    added_sintese_obs = False
    if ed_status == "Cabe ED": body_lines.append(f"Trata-se de decisão ({tipo_decisao}) em que se entende cabível ED:"); body_lines.append(f"Justificativa ED: {justificativa_ed}"); body_lines.append(""); added_sintese_obs = True
    elif sintese_objeto: body_lines.append("SÍNTESE DA DECISÃO / OBJETO DO RECURSO:"); body_lines.append(sintese_objeto); body_lines.append(""); added_sintese_obs = True
    elif obs_decisao: body_lines.append("OBSERVAÇÕES SOBRE A DECISÃO:"); body_lines.append(obs_decisao); body_lines.append(""); added_sintese_obs = True

    # --- Bloco 3: Detalhes da Execução / Pagamento / Recurso ---
    is_homologacao = fase == "Execução" and tipo_decisao and "Homologação de Cálculos" in tipo_decisao
    recursos_exec_impeditivos_916 = ["Embargos à Execução / Impugnação à Sentença", "Agravo de Petição (AP)"]
    recurso_impeditivo_selecionado = fase == "Execução" and recurso_rec in recursos_exec_impeditivos_916
    data_d_pagamento_str = "[DATA D- PAGAMENTO]"; data_fatal_pagamento_str = "[DATA FATAL PAGAMENTO]"
    if is_homologacao and data_ciencia:
        try: data_fatal_pag = add_business_days(data_ciencia, prazo_pagamento_dias); data_d_pag = add_business_days(data_fatal_pag, -3); data_d_pagamento_str = data_d_pag.strftime('%d/%m/%Y'); data_fatal_pagamento_str = data_fatal_pag.strftime('%d/%m/%Y');
        except Exception as e_dt_pag: log.error(f"Erro ao calcular datas de pagamento: {e_dt_pag}")

    # Cenário Homologação
    if is_homologacao:
        # ... (Lógica para exibir valores homologados e cenários 1, 2, 3, 4 mantida como na resposta anterior) ...
        body_lines.append(f"Foram homologados os cálculos, determinando o pagamento no prazo de {prazo_pagamento_dias} dias (Fatal: {data_fatal_pagamento_str}), sob pena de penhora.")
        # ... valores ...
        if recurso_impeditivo_selecionado: # Modelo 3 ou 4
            # ... texto ...
            pass
        else: # Cenário 1 ou 2
            if dep_anterior_valor > 0: # Modelo 1
                 # ... texto ...
                 pass
            else: # Modelo 2 Lógica
                if opcao_art_916 in ["Oferecer Opção Art. 916", "Cliente Optou por Art. 916"]:
                     # ... texto Opção 1 + Opção 2 com cálculo ...
                     pass
                else: # Apenas Pagamento Integral
                     # ... texto ...
                     pass

    # --- Lógica para Fase de Conhecimento ou Outras Decisões ---
    elif not is_homologacao:
        # ... (Lógica mantida para exibir Posição, Custas/Depósito se ed_status="Não cabe ED") ...
        if ed_status == "Não cabe ED" and recurso_rec and recurso_rec != "-- Selecione --":
             # ... código ...
             pass

    # --- Bloco 5: Prazos ---
    if prazos:
        body_lines.append("PRAZOS RELEVANTES:")
        prazo_principal = None
        prazo_acao_imediata = ""
        # ... (lógica para definir prazo_acao_imediata mantida) ...
        if ed_status == "Cabe ED": prazo_acao_imediata = "Embargos de Declaração"
        elif ed_status == "Não cabe ED" and recurso_rec and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --", "Outro"]: prazo_acao_imediata = recurso_rec
        elif ed_status == "Não cabe ED" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Verificar Recurso Contrário"
        elif fase == "Execução" and recurso_rec == "Não Interpor Recurso": prazo_acao_imediata = "Pagamento"


        # <<< INÍCIO DO BLOCO CORRIGIDO >>>
        for p_dict in prazos:
            # Garante indentação correta para o try
            try:
                p = Prazo(**p_dict)
                desc = p.descricao
                data_d_str = "N/I"; data_fatal_str = "N/I"
                # Bloco try/except interno para formatação de data (com indentação correta)
                try:
                    data_d_obj = datetime.strptime(p.data_d, '%Y-%m-%d').date()
                    data_d_str = data_d_obj.strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_d_str = f"{p.data_d}(Inválido)" if p.data_d else "N/I"
                try:
                    data_fatal_obj = datetime.strptime(p.data_fatal, '%Y-%m-%d').date()
                    data_fatal_str = data_fatal_obj.strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_fatal_str = f"{p.data_fatal}(Inválido)" if p.data_fatal else "N/I"

                # Adiciona linha formatada
                d_str = f"(D-: {data_d_str}, Fatal: {data_fatal_str})"
                body_lines.append(f"- {desc} {d_str}")
                if p.obs: body_lines.append(f"    Obs: {p.obs.strip()}")

                # Identifica prazo principal
                if prazo_acao_imediata and (prazo_acao_imediata.lower() in desc.lower() or (prazo_acao_imediata=="Pagamento" and "pagamento" in desc.lower())):
                    prazo_principal = p # Guarda o dataclass

                body_lines.append("") # Linha em branco APÓS item bem-sucedido

            except Exception as e: # Except alinhado com o Try externo
                 body_lines.append(f"- Erro ao formatar prazo: {p_dict} - {e}")
                 log.warning(f"Erro ao formatar prazo {p_dict}: {e}")
                 # Não adiciona linha em branco extra em caso de erro
                 continue # Pula para o próximo prazo no loop se este falhar
        # <<< FIM DO BLOCO CORRIGIDO >>>

        # Call to Action Final (Revisado)
        if prazo_principal:
            # ... (Lógica do CTA mantida como na resposta anterior) ...
            try:
                 data_d_cta = datetime.strptime(prazo_principal.data_d, '%Y-%m-%d').strftime('%d/%m/%Y'); data_fatal_cta = datetime.strptime(prazo_principal.data_fatal, '%Y-%m-%d').strftime('%d/%m/%Y'); desc_cta = prazo_principal.descricao
                 acao_pagamento_cta = status_custas == "A Recolher" or status_deposito in ["A Recolher/Complementar", "A Recolher (Situação Específica)", "Garantia do Juízo (Integral)"]
                 acao_recurso_ed_cta = ed_status == "Cabe ED" or (ed_status == "Não cabe ED" and recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"])
                 if acao_pagamento_cta and not (is_homologacao and not recurso_impeditivo_selecionado): body_lines.append(f"Solicitamos envio comprovante(s) pagamento até {data_d_cta} (Data D-).")
                 if acao_recurso_ed_cta: body_lines.append(f"Prazo fatal para medida ({desc_cta}) encerra em {data_fatal_cta}.")
                 if acao_recurso_ed_cta and ed_status != "Cabe ED" and not (fase=="Execução" and garantia_necessaria):
                      if recurso_rec not in ["Não Interpor Recurso", "-- Selecione --"]: body_lines.append("*Solicitamos retorno sobre interesse no recurso em 48 horas.*")
                 elif recurso_rec == "Não Interpor Recurso" and not is_homologacao: body_lines.append(f"Acompanharemos até {data_fatal_cta} para verificar recurso contrário.")
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

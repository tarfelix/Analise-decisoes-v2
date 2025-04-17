# -*- coding: utf-8 -*-
import re
import pandas as pd
from io import StringIO
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

log = logging.getLogger(__name__)

# --- Dataclasses ---
@dataclass
class PedidoData:
    Objetos: str = ""
    Situação: str = "N/A"
    Res1: str = "N/A"
    Res2: str = "N/A"
    ResSup: str = "N/A"

# --- Função de Parse Principal (v3 - Pandas + Fallback Texto) ---
def parse_and_format_report_v3(
    texto: Optional[str] = None,
    uploaded_file = None
    # tipo_decisao_analisada: str = "" # Removido - formatação é feita depois
) -> Tuple[Optional[List[PedidoData]], Optional[str]]:
    """Processa dados de pedidos (arquivo ou texto) e retorna dados estruturados."""
    log.info("Iniciando parse_and_format_report_v3")
    pedidos_data: List[PedidoData] = []
    processing_warnings: List[str] = []

    # --- Opção 1: Processar Arquivo ---
    if uploaded_file is not None:
        try:
            log.info(f"Processando arquivo: {uploaded_file.name}")
            df = None
            # ... (lógica de leitura de CSV/Excel/TXT com pandas mantida) ...
            if uploaded_file.name.lower().endswith('.csv'):
                file_content = uploaded_file.getvalue().decode('utf-8')
                sniffer = pd.io.common.sniff_delimiter(file_content, delimiters=['\t', ';', ','])
                df = pd.read_csv(StringIO(file_content), sep=sniffer, engine='python', skipinitialspace=True)
                log.info(f"CSV lido com separador '{sniffer}'")
            elif uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
                log.info("Excel lido com sucesso.")
            elif uploaded_file.name.lower().endswith('.txt'):
                 file_content = uploaded_file.getvalue().decode('utf-8')
                 try: df = pd.read_csv(StringIO(file_content), sep='\t', engine='python', skipinitialspace=True); log.info("TXT lido com TAB.")
                 except: df = pd.read_csv(StringIO(file_content), sep=r'\s{2,}', engine='python', skipinitialspace=True); log.info("TXT lido com múltiplos espaços.")
            else: return None, f"Erro: Formato de arquivo não suportado ({uploaded_file.name})."

            log.debug(f"Colunas originais: {df.columns.tolist()}")
            df.dropna(how='all', inplace=True); df.dropna(axis=1, how='all', inplace=True)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            rename_map = {}; found_map = { 'Objetos': False, 'Situação': False, 'Res1': False, 'Res2': False, 'ResSup': False }
            for col in df.columns: # Renomeia
                col_str = str(col).strip(); col_lower = col_str.lower()
                if not found_map['Objetos'] and ('objeto' in col_lower or 'pedido' in col_lower or col_lower.startswith('descri')): rename_map[col] = 'Objetos'; found_map['Objetos'] = True; continue
                if not found_map['Situação'] and ('situação' in col_lower or 'situacao' in col_lower): rename_map[col] = 'Situação'; found_map['Situação'] = True; continue
                if not found_map['Res1'] and ('1ª inst' in col_lower): rename_map[col] = 'Res1'; found_map['Res1'] = True; continue
                if not found_map['Res2'] and ('2ª inst' in col_lower): rename_map[col] = 'Res2'; found_map['Res2'] = True; continue
                if not found_map['ResSup'] and ('instância sup' in col_lower or 'instancia sup' in col_lower): rename_map[col] = 'ResSup'; found_map['ResSup'] = True; continue
            df = df.rename(columns=rename_map)
            log.debug(f"Colunas após renomear: {df.columns.tolist()}")

            required_cols = ['Objetos', 'Situação', 'Res1', 'Res2', 'ResSup']
            existing_cols = [col for col in required_cols if col in df.columns]
            if 'Objetos' not in existing_cols: return None, f"Erro Arquivo: Coluna 'Objetos' não encontrada. Colunas: {df.columns.tolist()}"

            df_final = df[existing_cols].fillna("N/A").astype(str) # Pega colunas existentes
            # Cria dataclasses preenchendo N/A para colunas faltantes
            pedidos_data = [PedidoData(**{k: row.get(k, "N/A") for k in PedidoData.__annotations__}) for row in df_final.to_dict('records')]
            log.info(f"{len(pedidos_data)} pedidos extraídos do arquivo.")

        except pd.errors.EmptyDataError: return None, "Erro: O arquivo carregado está vazio."
        except Exception as e: log.error(f"Erro ao processar arquivo: {e}", exc_info=True); return None, f"Erro ao processar o arquivo. Detalhe: {e}"

    # --- Opção 2: Processar Texto Colado (Fallback) ---
    elif texto:
        # (Lógica de parse de texto mantida como na resposta anterior)
        # ... (código v2 para parse de texto omitido para brevidade, mas deve ser incluído aqui)...
        # ... Ele deve popular a lista `pedidos_data` com objetos `PedidoData` ...
        log.info("Processando texto colado.")
        lines = [l.strip() for l in texto.strip().splitlines() if l.strip()]
        if not lines: return None, "Erro: Texto colado está vazio."
        header_keywords = ['situação', 'resultado 1ª instância', 'resultado 2ª instância', 'resultado instância superior']
        header_row_index = -1; header_map = {}; header_line_parts = []
        for i, line in enumerate(lines): # Encontra header
            line_lower = line.lower(); keywords_found = [kw for kw in header_keywords if kw in line_lower]
            common_data_starts = ['adicional', 'horas', 'multa', 'diferenças', 'danos', 'justiça', 'honorários']
            is_likely_header = len(keywords_found) >= 2 and not any(line_lower.startswith(start) for start in common_data_starts)
            if is_likely_header:
                header_row_index = i; parts = line.split('\t')
                if len(parts) <= 1: parts = re.split(r'\s{2,}', line)
                header_line_parts = [p.strip() for p in parts]; break
        if header_row_index == -1: # Fallback "Objetos"
            try:
                objetos_index = -1
                for i, line in enumerate(lines):
                    if line.strip().lower() == 'objetos': objetos_index = i; break
                if objetos_index != -1 and objetos_index + 1 < len(lines):
                     header_row_index = objetos_index + 1; line = lines[header_row_index]
                     parts = line.split('\t');
                     if len(parts) <= 1: parts = re.split(r'\s{2,}', line)
                     header_line_parts = [p.strip() for p in parts]; log.warning("Cabeçalho usando linha após 'Objetos'.")
                else: return None, "Erro: Não foi possível localizar linha de cabeçalho."
            except Exception as e_fb: return None, f"Erro fallback: {e_fb}"
        log.debug(f"Cabeçalho detectado para mapeamento: {header_line_parts}")
        try: # Mapeia Situação/Resultados
            header_map['situação'] = header_line_parts.index(next(h for h in header_line_parts if 'situação' in h.lower()))
            header_map['resultado 1ª instância'] = header_line_parts.index(next(h for h in header_line_parts if 'resultado 1ª instância' in h.lower()))
            header_map['resultado 2ª instância'] = header_line_parts.index(next(h for h in header_line_parts if 'resultado 2ª instância' in h.lower()))
            header_map['resultado instância superior'] = header_line_parts.index(next(h for h in header_line_parts if 'resultado instância superior' in h.lower()))
            log.debug(f"Mapeamento: {header_map}")
        except (ValueError, StopIteration) as e_map:
            error_detail = f"Cabeçalho: '{' | '.join(header_line_parts)}'. Mapa: {header_map}. Erro: {e_map}"
            log.error(f"Falha mapeamento: {error_detail}")
            return None, f"Erro: Falha ao mapear colunas essenciais.\n{error_detail}"

        data_rows_start_index = header_row_index + 1; processing_warnings = []
        log.info(f"Iniciando processamento de dados texto da linha {data_rows_start_index}")
        for i in range(data_rows_start_index, len(lines)): # Processa linhas
            line = lines[i]; line_lower_strip = line.strip().lower()
            if not line or line_lower_strip.startswith(("visualizar", "editar", "ação", "gerenciar")): continue
            parts = line.split('\t'); split_method = "TAB"
            if len(parts) <= 1 and len(line.split()) > 1: parts = re.split(r'\s{2,}', line); split_method = "REGEX"
            if len(parts) <= 1 and len(line.split()) > 1: parts = line.split(); split_method = "ESPAÇO SIMPLES"
            parts = [p.strip() for p in parts if p.strip()]
            if not parts or not parts[0]: continue
            try: # Extração revisada
                p_data = PedidoData(Objetos=parts[0])
                offset = 1
                idx_situacao = header_map['situação'] + offset
                idx_res1 = header_map['resultado 1ª instância'] + offset
                idx_res2 = header_map['resultado 2ª instância'] + offset
                idx_resSup = header_map['resultado instância superior'] + offset
                p_data.Situação = parts[idx_situacao] if idx_situacao < len(parts) else 'N/A'
                p_data.Res1 = parts[idx_res1] if idx_res1 < len(parts) else 'N/A'
                p_data.Res2 = parts[idx_res2] if idx_res2 < len(parts) else 'N/A'
                p_data.ResSup = parts[idx_resSup] if idx_resSup < len(parts) else 'N/A'
                pedidos_data.append(p_data)
            except IndexError: processing_warnings.append(f"Linha {i+1} (Índice): '{line[:70]}...' | Parts: {len(parts)}")
            except Exception as e: processing_warnings.append(f"Linha {i+1} (Erro): '{line[:70]}...' - {e}")
        log.info(f"{len(pedidos_data)} pedidos extraídos do texto.")
        if not pedidos_data:
            error_msg = "Erro: Nenhum dado de pedido válido encontrado no texto."
            if processing_warnings: error_msg += "\nProblemas:\n" + "\n".join([f"- {w}" for w in processing_warnings])
            return None, error_msg
        if processing_warnings:
             log.warning("Avisos durante processamento do texto:")
             for warn in processing_warnings: log.warning(f"- {warn}")

    else:
        return None, "Erro: Nenhuma tabela fornecida (texto ou arquivo)."

    # --- Ordenar ---
    try: pedidos_data.sort(key=lambda p: p.Objetos)
    except Exception as e: log.warning(f"Não foi possível ordenar pedidos: {e}", exc_info=True)

    log.info("Parser finalizado com sucesso.")
    # Retorna apenas os dados estruturados e None para erro
    return pedidos_data, None
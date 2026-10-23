"""Conservative, auditable security eligibility checks. Unknowns are NOT confirmed equities."""
import re

BAD_NAME = re.compile(r'\b(acquisition corp(?:oration)?|acquisition co\.?|blank.check|special purpose acquisition|\bspac\b|warrants?|rights?|units?|depositary units?|exchange.traded|\betf\b|\betn\b|closed.end fund|trust units|preferred (shares|stock)|preferred series|notes due|senior notes)\b',re.I)
BAD_TICKER = re.compile(r'(?:W|WS|WT|U|R)$')

def evaluate_security(ticker, company_name='', instrument_type=None):
    """Name-screen is intentionally conservative; no claim of 100% SPAC detection."""
    t=str(ticker or '').upper().strip(); name=str(company_name or '').strip()
    if not t or not re.fullmatch(r'[A-Z]{1,6}',t): return 'EXCLUIDO','Ticker no ordinario'
    if instrument_type and instrument_type not in ('EQUITY','COMMON_STOCK'):
        return 'EXCLUIDO',f'Tipo de instrumento: {instrument_type}'
    if name and BAD_NAME.search(name): return 'EXCLUIDO','Emisor/instrumento no elegible por nombre'
    if not name: return 'SIN VERIFICAR','Falta nombre de emisor para verificar elegibilidad'
    # Do not exclude ending W/U/R alone: these are legitimate ordinary tickers too.
    return 'APTO PROVISIONAL','Filtro de nombre superado; clase de título no verificada independientemente'

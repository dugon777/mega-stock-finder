"""Discover SEC-listed common-stock candidates; fallback to a local file, always pin watchlist."""
import json
import os
from pathlib import Path
import requests

SEC_URL = 'https://www.sec.gov/files/company_tickers_exchange.json'
EXCHANGES = {'Nasdaq', 'NYSE', 'NYSE American', 'Cboe BZX'}

def tickers_from_sec(payload):
    fields = payload.get('fields', [])
    if not {'ticker', 'exchange'}.issubset(fields):
        raise ValueError('SEC response missing fields')
    ix = {name: fields.index(name) for name in fields}
    out = {}
    for row in payload.get('data', []):
        ticker = str(row[ix['ticker']]).strip().upper()
        exchange = str(row[ix['exchange']]).strip()
        # SEC registry includes other security types. Exclude obvious non-common symbols;
        # this is NOT a guarantee that all remaining securities are common stock.
        if exchange in EXCHANGES and 1 <= len(ticker) <= 6 and ticker.isalpha():
            name=str(row[ix['name']]) if 'name' in ix else ''
            out[ticker]=name
    return dict(sorted(out.items()))

def discover(root):
    pinned = sorted({line.strip().upper() for line in (root/'universe.txt').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')})
    cached = root/'scanner'/'universe_cache.json'
    sources = ['SEC', 'cached SEC', 'watchlist only']
    try:
        ua = os.getenv('SEC_USER_AGENT', '').strip()
        if not ua or '@' not in ua:
            raise RuntimeError('SEC_USER_AGENT missing: set a descriptive contact email in GitHub Actions secrets')
        response = requests.get(SEC_URL, headers={'User-Agent': ua, 'Accept-Encoding':'gzip, deflate', 'Accept':'application/json'}, timeout=25)
        response.raise_for_status()
        universe = tickers_from_sec(response.json())
        if len(universe) < 1000: raise RuntimeError('SEC universe unexpectedly small')
        cached.write_text(json.dumps(universe), encoding='utf-8')
        source = sources[0]
    except Exception as exc:
        print('SEC universe unavailable:', str(exc)[:180])
        try:
            universe = json.loads(cached.read_text(encoding='utf-8'))
            source = sources[1]
        except (OSError,ValueError):
            universe = {}
            source = sources[2]
    if isinstance(universe,list): universe={t:'' for t in universe}
    return dict(sorted({**universe, **{t:universe.get(t,'') for t in pinned}}.items())), pinned, source

"""Daily rotating SEC-listed universe scan; pinned watchlist scanned every session."""
import json, os, sys, time
from datetime import datetime, timezone, date
from pathlib import Path
from scanner.core import classify
from scanner.universe import discover
from scanner.eligibility import evaluate_security

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/data.json'

def fetch(symbol):
    try:
        import yfinance as yf
        frame=yf.Ticker(symbol).history(period='18mo',interval='1d',auto_adjust=True,actions=False,raise_errors=False)
        if frame.empty: return None
        if frame.index.tz is not None: frame.index=frame.index.tz_localize(None)
        return frame
    except Exception as e:
        print('Fetch failed',symbol,str(e)[:130],file=sys.stderr)
        return None

def select_batch(universe,pinned,scan_day,batch_size):
    pinned_set=set(pinned)
    rest=[x for x in universe if x not in pinned_set and evaluate_security(x,universe.get(x,''))[0]!='EXCLUIDO']
    if not rest: return pinned[:]
    # Contiguous rotating shards, deterministic across runs, no random selection.
    start=(scan_day.toordinal()*batch_size)%len(rest)
    selection=[rest[(start+i)%len(rest)] for i in range(min(batch_size,len(rest)))]
    return sorted(pinned_set)+selection

def main():
    universe,pinned,source=discover(ROOT)
    batch_size=max(20,min(1000,int(os.getenv('SCAN_BATCH_SIZE','250'))))
    asof=date.today()
    watch=select_batch(universe,pinned,asof,batch_size)
    try:
        old=json.loads(OUTPUT.read_text(encoding='utf-8'))
        previous={r['ticker']:r for r in old.get('results',[]) if r.get('ticker') in universe and 'eligibility' in r and 'score_parts' in r}
    except (OSError,ValueError,KeyError):
        previous={}
    market=fetch('SPY')
    if market is None: raise RuntimeError('SPY unavailable: cannot validate relative strength')
    newly_valid=0; failed=0
    for i,ticker in enumerate(watch):
        print(f'{i+1}/{len(watch)} {ticker}',flush=True)
        eligible,eligibility_reason=evaluate_security(ticker,universe.get(ticker,''))
        if eligible=='EXCLUIDO':
            previous.pop(ticker,None)
            continue
        df=fetch(ticker)
        try:
            value=classify(df,market)
        except Exception as e:
            value={'status':'ERROR','reason':str(e)[:140]}
        value['ticker']=ticker
        value['company_name']=universe.get(ticker,'')
        value['eligibility']=eligible
        value['eligibility_reason']=eligibility_reason
        if eligible=='SIN VERIFICAR':
            value['status']='VERIFICAR INSTRUMENTO'
            value['score']=None
        if value.get('score') is None and value.get('signal_quality')!='NO EVALUABLE':
            value['ranking_eligible']=False
        else: value['ranking_eligible']=bool(eligible=='APTO PROVISIONAL' and value.get('score') is not None)
        value['last_checked_utc']=datetime.now(timezone.utc).isoformat()
        if value.get('price') is not None:
            newly_valid+=1
            previous[ticker]=value
        elif ticker not in previous:
            failed+=1
            previous[ticker]=value
        else:
            failed+=1
            previous[ticker]['last_attempt_utc']=value['last_checked_utc']
            previous[ticker]['last_attempt_status']=value['status']
        time.sleep(float(os.getenv('REQUEST_PAUSE_SECONDS','0.25')))
    # Invalidate previously stored classifications created by the old scoring system.
    results=sorted((r for r in previous.values() if r.get('eligibility')=='APTO PROVISIONAL'),
      key=lambda x:(not x.get('ranking_eligible',False),-(x.get('score') or 0),x['ticker']))
    out={'generated_at_utc':datetime.now(timezone.utc).isoformat(),
         'universe_source':source,'universe_size':len(universe),'pinned_watchlist':pinned,
         'attempted_this_run':len(watch),'successful_this_run':newly_valid,
         'failed_this_run':failed,'stored_results':len(results),
         'data_source':'Yahoo Finance / yfinance no oficial; sin garantía de cobertura o permisos de redistribución',
         'benchmark':'SPY (proxy, no los tres índices cash)',
         'results':results,'notice':'Cobertura acumulada POR LOTES; cada fila indica la fecha de su precio y última revisión. No es CAN SLIM completo ni buy signal validado.'}
    if newly_valid==0:
        raise RuntimeError('Zero fresh valid symbols; refusing to publish stale scan as new success')
    OUTPUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Universe',len(universe),'attempted',len(watch),'good',newly_valid,'historical records',len(results))

if __name__=='__main__': main()

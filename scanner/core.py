"""Daily EOD technical scanner. Approximate technical candidates, never official IBD signals."""
import math
import numpy as np
import pandas as pd


def number(v, n=2):
    try:
        return round(float(v),n) if math.isfinite(float(v)) else None
    except (TypeError,ValueError):
        return None


def classify(df, market=None):
    if df is None or len(df)<210:
        return {"status":"DATOS INSUFICIENTES", "reason":"Menos de 210 sesiones válidas"}
    d=df.copy().dropna(subset=['Close','High','Low','Volume'])
    if len(d)<210: return {"status":"DATOS INSUFICIENTES", "reason":"Historial incompleto"}
    c=d['Close'].astype(float); h=d['High'].astype(float); l=d['Low'].astype(float); v=d['Volume'].astype(float)
    ma20=c.rolling(20).mean().iloc[-1]; ma50=c.rolling(50).mean().iloc[-1]; ma200=c.rolling(200).mean().iloc[-1]
    px=float(c.iloc[-1]); ref=float(h.iloc[-41:-1].max()); avgvol=float(v.iloc[-51:-1].mean()); volrel=float(v.iloc[-1]/avgvol) if avgvol>0 else None
    dist50=(px/ma50-1)*100; dist200=(px/ma200-1)*100; distpivot=(px/ref-1)*100
    ret20=(px/c.iloc[-21]-1)*100; ret63=(px/c.iloc[-64]-1)*100
    low_now=float(l.iloc[-20:].min()); low_prev=float(l.iloc[-40:-20].min()); higher_low=low_now>low_prev
    market_lower=None; rs20=None
    if market is not None and len(market)>=42:
        # Align dates to avoid comparing disjoint market sessions
        m=market.reindex(d.index).ffill()['Close'].dropna()
        if len(m)>=41:
            mlow=market.reindex(d.index).ffill()['Low'].dropna()
            market_lower=bool(mlow.iloc[-20:].min()<mlow.iloc[-40:-20].min())
            if len(m)>=21: rs20=ret20-(float(m.iloc[-1]/m.iloc[-21])-1)*100
    smt=(higher_low and market_lower) if market_lower is not None else None
    trend=(px>ma50>ma200)
    extended=(dist50>15 or distpivot>5)
    breakout=(px>ref and volrel is not None and volrel>=1.4 and trend and 0<=distpivot<=5)
    if extended: status='EXTENDIDA / NO PERSEGUIR'
    elif breakout: status='RUPTURA PROVISIONAL'
    elif 0<=distpivot<=5 and trend: status='EN ZONA DE VIGILANCIA'
    elif px>ma200 and abs(dist50)<8: status='BASE POTENCIAL'
    else: status='SIN SETUP'
    score = (25 if px>ma200 else 0)+(20 if ma50>ma200 else 0)+(20 if (rs20 is not None and rs20>0) else 0)+(15 if smt else 0)+(20 if (not extended and -5<=distpivot<=5) else 0)
    return dict(status=status,score=score,date=str(d.index[-1].date()),price=number(px),ma20=number(ma20),ma50=number(ma50),ma200=number(ma200),dist50_pct=number(dist50),dist200_pct=number(dist200),reference_high_40d=number(ref),dist_ref_pct=number(distpivot),volume_multiple=number(volrel),return_20d_pct=number(ret20),return_63d_pct=number(ret63),relative_20d_spy_pp=number(rs20),smt_proxy=smt,above_ma200=bool(px>ma200),extended=bool(extended),reason='Referencia = máximo de los 40 días anteriores; NO pivote CAN SLIM validado. SMT aproximada sobre ventanas, no swings confirmados.')

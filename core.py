"""Conservative preliminary EOD scanner. NOT official CAN SLIM or IBD rating."""
import math
import numpy as np
import pandas as pd

def number(v,n=2):
    try:
        return round(float(v),n) if math.isfinite(float(v)) else None
    except (TypeError,ValueError): return None

def classify(df,market=None):
    bad={'status':'DATOS INSUFICIENTES','score':None,'signal_quality':'NO EVALUABLE'}
    if df is None or len(df)<210: return dict(bad,reason='Menos de 210 sesiones')
    d=df.copy().dropna(subset=['Close','High','Low','Volume']).sort_index()
    if len(d)<210: return dict(bad,reason='Historial incompleto')
    c=d.Close.astype(float); h=d.High.astype(float); l=d.Low.astype(float); v=d.Volume.astype(float)
    if not (np.isfinite(c).all() and np.isfinite(v).all() and (c>0).all() and (v>=0).all()):
        return dict(bad,reason='Valores de precio/volumen inválidos')
    px=float(c.iloc[-1]); ma20=float(c.iloc[-20:].mean()); ma50=float(c.iloc[-50:].mean()); ma200=float(c.iloc[-200:].mean())
    ref=float(h.iloc[-41:-1].max()); avgvol=float(v.iloc[-51:-1].mean()); lastvol=float(v.iloc[-1]); volrel=lastvol/avgvol if avgvol>0 else None
    dollarvol=float((c.iloc[-50:]*v.iloc[-50:]).median()); dist50=(px/ma50-1)*100; dist200=(px/ma200-1)*100; distpivot=(px/ref-1)*100
    ret20=(px/c.iloc[-21]-1)*100; ret63=(px/c.iloc[-64]-1)*100
    rs20=None; smt=None
    if market is not None and len(market)>42:
        # Strict common-date alignment: no forward-filling old market prices.
        aligned=d[['Close','Low']].join(market[['Close','Low']],how='inner',rsuffix='_market').dropna()
        if len(aligned)>=41 and aligned.index[-1].date()==d.index[-1].date():
            mret=(float(aligned.Close_market.iloc[-1])/float(aligned.Close_market.iloc[-21])-1)*100
            stockret=(float(aligned.Close.iloc[-1])/float(aligned.Close.iloc[-21])-1)*100
            rs20=stockret-mret
            higher_low=float(aligned.Low.iloc[-20:].min())>float(aligned.Low.iloc[-40:-20].min())
            market_lower=float(aligned.Low_market.iloc[-20:].min())<float(aligned.Low_market.iloc[-40:-20].min())
            smt=higher_low and market_lower
    # Hard stop on penny stocks, illiquidity, missing volume and delayed data.
    date_=pd.Timestamp(d.index[-1]).date(); today=pd.Timestamp.now(tz='America/New_York').date()
    age=int(np.busday_count(date_.isoformat(),today.isoformat())) if today>=date_ else 0
    adequate=px>=5 and dollarvol>=1_000_000 and avgvol>=50_000 and lastvol>0 and volrel is not None
    fresh=age<=2
    extended=dist50>15 or distpivot>5 or ret20>30
    trend=px>ma50>ma200
    breakout=px>ref and volrel is not None and volrel>=1.4 and trend and 0<=distpivot<=5
    if not fresh: status='DATOS DESACTUALIZADOS'
    elif not adequate: status='DESCARTADA: LIQUIDEZ/PRECIO'
    elif extended: status='EXTENDIDA / NO PERSEGUIR'
    elif breakout: status='RUPTURA PROVISIONAL'
    elif -3<=distpivot<=5 and trend: status='EN ZONA DE VIGILANCIA'
    elif px>ma200 and abs(dist50)<8 and abs(distpivot)<12: status='BASE POTENCIAL'
    else: status='SIN SETUP'
    # 100-point transparent technical score (no implicit bonus for missing data).
    parts={'trend':20 if trend else 0,'long_term':10 if px>ma200 else 0,
           'rs':20 if rs20 is not None and rs20>5 else (10 if rs20 is not None and rs20>0 else 0),
           'volume':15 if breakout else (8 if volrel is not None and volrel>1.2 and px>c.iloc[-2] else 0),
           'position':20 if -3<=distpivot<=3 else (10 if -8<=distpivot<=5 else 0),
           'smt_proxy':15 if smt is True else 0}
    score=sum(parts.values()) if adequate and fresh and rs20 is not None and not extended else None
    return dict(status=status,score=score,score_parts=parts,signal_quality='SOLO TECNICA; FUNDAMENTALES NO VALIDADOS',
                date=date_.isoformat(),price=number(px),ma20=number(ma20),ma50=number(ma50),ma200=number(ma200),
                dist50_pct=number(dist50),dist200_pct=number(dist200),reference_high_40d=number(ref),dist_ref_pct=number(distpivot),
                volume_multiple=number(volrel),avg_dollar_volume_50d=number(dollarvol,0),return_20d_pct=number(ret20),
                return_63d_pct=number(ret63),relative_20d_spy_pp=number(rs20),smt_proxy=smt,
                above_ma200=bool(px>ma200),extended=bool(extended),data_age_business_days=age,
                reason='Pivot 40d no validado. SMT es proxy vs SPY, no divergencia ICT verificada. No hay datos CAN SLIM fundamentales.')

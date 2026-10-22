from datetime import date
from scanner.universe import tickers_from_sec
from scanner.run import select_batch

def test_discovery_exchanges():
    obj={'fields':['cik','name','ticker','exchange'],'data':[[1,'A','PAY','NYSE'],[2,'B','CLFD','Nasdaq'],[3,'C','TEST','OTC'],[4,'D','BRK-B','NYSE']]}
    assert tickers_from_sec(obj)==['CLFD','PAY']

def test_pinned_in_every_batch():
    universe=['A','B','C','D','PAY','GLBE']
    for day in [date(2026,10,22),date(2026,10,23)]:
        selected=select_batch(universe,['PAY','GLBE'],day,2)
        assert 'PAY' in selected and 'GLBE' in selected
        assert len(selected)==4

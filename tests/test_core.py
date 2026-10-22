import unittest
import pandas as pd
from scanner.core import classify
class TestCore(unittest.TestCase):
    def test_short_history(self):
        self.assertEqual(classify(pd.DataFrame()).get('status'),'DATOS INSUFICIENTES')
    def test_flat_history(self):
        n=240; ix=pd.date_range('2025-01-01',periods=n,freq='B');x=pd.DataFrame({'Close':[100.0]*n,'High':[101.0]*n,'Low':[99.0]*n,'Volume':[1000]*n},index=ix)
        r=classify(x,x);self.assertEqual(r['price'],100);self.assertEqual(r['status'],'SIN SETUP');self.assertEqual(r['extended'],False)
if __name__=='__main__':unittest.main()

import unittest,tempfile,hashlib
from pathlib import Path
import pandas as pd

class ReviewRegressionTests(unittest.TestCase):
    def test_changed_workbook_replaces_stale_values_and_fingerprint(self):
        from retail_core import load_source
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.xlsx'
            pd.DataFrame({'Invoice':['old'],'Quantity':[1]}).to_excel(source,index=False)
            first,first_hash=load_source(source)
            first.to_pickle(Path(directory)/'retail.pkl')
            pd.DataFrame({'Invoice':['new'],'Quantity':[9]}).to_excel(source,index=False)
            second,second_hash=load_source(source)
            self.assertEqual(second.Quantity.tolist(),[9])
            self.assertNotEqual(first_hash,second_hash)
            self.assertEqual(second_hash,hashlib.sha256(source.read_bytes()).hexdigest())

    def test_small_gold_text_contrast(self):
        page=(Path(__file__).resolve().parents[1]/'projects/retail-analysis.html').read_text(encoding='utf8')
        import re
        color=re.search(r'--gold:(#[0-9a-f]{6})',page)[1]
        def luminance(c):
            vals=[int(c[i:i+2],16)/255 for i in (1,3,5)]
            vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]
            return sum(v*w for v,w in zip(vals,[.2126,.7152,.0722]))
        self.assertGreaterEqual((luminance('#faf9f5')+.05)/(luminance(color)+.05),4.5)

if __name__=='__main__':unittest.main()

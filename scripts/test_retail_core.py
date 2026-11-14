import unittest
import pandas as pd
from retail_core import classify_rows, match_credits

def frame(rows):
    df = pd.DataFrame(rows, columns=['Invoice','StockCode','Quantity','Price','Customer ID','Country','InvoiceDate'])
    df['InvoiceDate']=pd.to_datetime(df.InvoiceDate)
    return df

class RetailCoreTests(unittest.TestCase):
    def test_missing_customer_still_counts_and_nonstock_is_separate(self):
        df=frame([['1','12345',2,4,None,'UK','2011-01-01'],['C2','12345',-1,4,None,'UK','2011-01-02'],['C3','M',-1,20,'1','UK','2011-01-02'],['4','12345',-1,0,None,'UK','2011-01-02']])
        self.assertEqual(classify_rows(df).tolist(),['product_sale','product_credit','nonproduct','zero_value'])

    def test_quantity_cannot_be_reused_and_later_sale_does_not_match(self):
        df=frame([['1','12345',5,2,'a','UK','2011-01-01'],['C2','12345',-3,2,'a','UK','2011-01-02'],['C3','12345',-4,2,'a','UK','2011-01-03'],['4','12345',9,2,'a','UK','2011-01-04']])
        matched=match_credits(df)
        self.assertEqual(matched.matched_qty.tolist(),[3,2])
        self.assertEqual(matched.unmatched_qty.tolist(),[0,2])

    def test_matching_requires_identified_customer_country_and_price(self):
        df=frame([['1','12345',10,2,'a','UK','2011-01-01'],['C2','12345',-1,3,'a','UK','2011-01-02'],['C3','12345',-1,2,'a','France','2011-01-02'],['C4','12345',-1,2,None,'UK','2011-01-02']])
        self.assertEqual(match_credits(df).matched_qty.sum(),0)

    def test_same_day_reversal_is_candidate_not_proven_return(self):
        df=frame([['1','12345',5,2,'a','UK','2011-01-01 10:00'],['C2','12345',-2,2,'a','UK','2011-01-01 10:05']])
        self.assertEqual(match_credits(df).same_day_qty.sum(),2)

if __name__=='__main__': unittest.main()

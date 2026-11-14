"""Explicit transaction classification and candidate cancellation matching.

Matching is a quantity-constrained heuristic, not proof of an original invoice.
"""
from collections import defaultdict
import pandas as pd
import numpy as np
from io import BytesIO
import hashlib

def load_source(source):
    """Read and fingerprint the same source bytes; never reuse a stale cache."""
    content=source.read_bytes()
    sheets=pd.read_excel(BytesIO(content),sheet_name=None,dtype={'Invoice':str,'StockCode':str,'Customer ID':str})
    raw=pd.concat([df.assign(sheet=name) for name,df in sheets.items()],ignore_index=True)
    return raw,hashlib.sha256(content).hexdigest()

def classify_rows(df):
    kind=pd.Series('anomaly',index=df.index,dtype='object')
    valid=np.isfinite(df.Quantity)&np.isfinite(df.Price)&df.InvoiceDate.notna()
    product=df.StockCode.astype(str).str.fullmatch(r'\d{5}[A-Za-z]{0,2}',na=False)
    credit=df.Invoice.astype(str).str.upper().str.startswith('C')
    positive=valid&(df.Price>0)
    kind.loc[positive&product&(df.Quantity>0)&~credit]='product_sale'
    kind.loc[positive&product&(df.Quantity<0)&credit]='product_credit'
    kind.loc[positive&~product]='nonproduct'
    kind.loc[valid&((df.Quantity==0)|(df.Price==0))]='zero_value'
    kind.loc[~valid|(df.Price<0)]='invalid_value'
    return kind

def match_credits(df):
    kinds=classify_rows(df)
    data=df.loc[kinds.isin(['product_sale','product_credit'])].copy()
    data['_is_credit']=(data.Quantity<0).astype(int)
    # Sales at the same timestamp precede credits, but are only candidate matches.
    data=data.sort_values(['InvoiceDate','_is_credit'],kind='stable')
    available=defaultdict(list)
    out=[]
    columns=['InvoiceDate','Customer ID','Country','StockCode','Price','Quantity']
    for idx,date,customer,country,stock,price,quantity in data[columns].itertuples(name=None):
        identified=pd.notna(customer) and str(customer).strip() not in ('','nan')
        key=(str(customer),str(country),str(stock),round(float(price),6))
        if quantity>0:
            if identified: available[key].append([float(quantity),date])
            continue
        remaining=-float(quantity); matched=0.; same_day=0.
        stack=available[key] if identified else []
        while remaining>0 and stack:
            qty,sale_date=stack[-1]
            take=min(qty,remaining)
            matched+=take;remaining-=take
            if sale_date.date()==date.date(): same_day+=take
            stack[-1][0]-=take
            if stack[-1][0]<=0: stack.pop()
        out.append({'row_index':idx,'matched_qty':matched,'unmatched_qty':remaining,'same_day_qty':same_day})
    return pd.DataFrame(out,columns=['row_index','matched_qty','unmatched_qty','same_day_qty'])

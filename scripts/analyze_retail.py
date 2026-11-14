"""Reproduce Online Retail II audit and aggregates. Raw customer IDs are never exported.

Download UCI source to data/raw/online_retail_II.xlsx, then run this script.
Requirements: pandas, openpyxl. See projects/retail-analysis.html for methodology.
"""
from pathlib import Path
import json, hashlib
import pandas as pd
import numpy as np
from retail_core import classify_rows, match_credits, load_source

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'projects/retail-data';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'data/raw/online_retail_II.xlsx'
raw,source_sha256=load_source(SOURCE)
cols=[c for c in raw.columns if c!='sheet']
# Same workbook has overlapping dates across two sheets. Preserve within-sheet multiplicity.
raw['_occurrence']=raw.groupby(cols+['sheet'],dropna=False,sort=False).cumcount()
overlap=raw.duplicated(cols+['_occurrence'],keep='first')
df=raw.loc[~overlap,cols].copy().reset_index(drop=True)
for col in ['Invoice','StockCode','Country']: df[col]=df[col].astype(str).str.strip()
df['kind']=classify_rows(df)
df['amount']=df.Quantity*df.Price
df['gross']=np.where(df.kind=='product_sale',df.amount,0.)
df['credit']=np.where(df.kind=='product_credit',-df.amount,0.)
df['month']=df.InvoiceDate.dt.strftime('%Y-%m')
df['row_index']=df.index
full=df[df.InvoiceDate.lt('2011-12-01')].copy()
product=full[full.kind.isin(['product_sale','product_credit'])].copy()
product['sale_invoice']=product.Invoice.where(product.kind=='product_sale')
product['credit_invoice']=product.Invoice.where(product.kind=='product_credit')

def aggregate(data,keys):
    g=data.groupby(keys,dropna=False).agg(gross=('gross','sum'),credit=('credit','sum'),rows=('Invoice','size'),sale_invoices=('sale_invoice','nunique'),credit_invoices=('credit_invoice','nunique'))
    g['net']=g.gross-g.credit
    g['credit_ratio_pct']=g.credit.div(g.gross.replace(0,np.nan))*100
    return g.reset_index()

monthly=aggregate(product,['month'])
countries=aggregate(product,['Country']).sort_values('credit',ascending=False)
sku=aggregate(product,['StockCode']).sort_values('credit',ascending=False)
country_sku=aggregate(product,['Country','StockCode']).sort_values('credit',ascending=False)
desc=product.loc[product.gross>0].groupby('StockCode').Description.agg(lambda s:s.dropna().mode().iloc[0] if len(s.dropna()) else '')
sku['Description']=sku.StockCode.map(desc)
country_sku['Description']=country_sku.StockCode.map(desc)
matches=match_credits(df)
matched=df.loc[matches.row_index].merge(matches,on='row_index',validate='one_to_one')
matched=matched[matched.InvoiceDate.lt('2011-12-01')].copy()
matched['matched_amount']=matched.matched_qty*matched.Price
matched['unmatched_amount']=matched.unmatched_qty*matched.Price
matched['same_day_amount']=matched.same_day_qty*matched.Price
match_country=matched.groupby('Country')[['matched_amount','unmatched_amount','same_day_amount']].sum().reset_index()
countries=countries.merge(match_country,on='Country',how='left').fillna({'matched_amount':0,'unmatched_amount':0,'same_day_amount':0})
countries['outside_same_day_credit']=countries.credit-countries.same_day_amount
countries['screened_ratio_pct']=countries.outside_same_day_credit/countries.gross*100
gross=float(product.gross.sum());credit=float(product.credit.sum())
quality=full.groupby('kind').agg(rows=('Invoice','size'),signed_amount=('amount','sum')).reset_index()
nonproduct=full[~full.kind.isin(['product_sale','product_credit'])].groupby(['kind','StockCode']).agg(rows=('Invoice','size'),signed_amount=('amount','sum')).reset_index().sort_values('signed_amount')
dups=full.duplicated(cols,keep='first')
dedup=product.loc[~product.index.isin(full.index[dups])]
dedup_country=aggregate(dedup,['Country'])
dedup_country=dedup_country.rename(columns={'gross':'dedup_gross','credit':'dedup_credit','credit_ratio_pct':'dedup_credit_ratio_pct'})
countries=countries.merge(dedup_country[['Country','dedup_gross','dedup_credit','dedup_credit_ratio_pct']],on='Country',how='left')
unidentified=product['Customer ID'].isna()
large=matched.sort_values('credit',ascending=False).head(15)
invoice_credits=product[product.credit>0].groupby('Invoice').credit.sum().sort_values(ascending=False)
country_eligible=countries[(countries.gross>=100000)&(countries.Country!='United Kingdom')&(~countries.Country.isin(['Unspecified','European Community']))].copy()
country_eligible=country_eligible.sort_values('credit',ascending=False)
fr=product[product.Country.eq('France')]
fr_invoices=fr[fr.credit>0].groupby('Invoice').agg(credit=('credit','sum'),lines=('Invoice','size'),products=('StockCode','nunique'),date=('InvoiceDate','min')).sort_values('credit',ascending=False)
focus_id=fr_invoices.index[0]
focus=fr[fr.Invoice.eq(focus_id)]
focus_customer=focus['Customer ID'].dropna().unique()
focus_matches=matched[matched.Invoice.eq(focus_id)]
candidate_sales=product[(product['Customer ID'].isin(focus_customer))&(product.Country.eq('France'))&(product.gross>0)&(product.InvoiceDate<=focus.InvoiceDate.min())]
candidate_sales=candidate_sales[candidate_sales.StockCode.isin(focus.StockCode)]
candidate_invoices=candidate_sales.groupby('Invoice').agg(gross=('gross','sum'),products=('StockCode','nunique'),date=('InvoiceDate','min')).sort_values('gross',ascending=False).head(8)

summary={
 'source_url':'https://archive.ics.uci.edu/dataset/502/online+retail+ii',
 'download_url':'https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip',
 'doi':'10.24432/C5CG6D','license':'CC BY 4.0','retrieved_on':'2026-11-14',
 'sha256':source_sha256,
 'raw_rows':len(raw),'cross_sheet_copies_removed':int(overlap.sum()),'canonical_rows':len(df),
 'full_period':'2009-12-01 to 2011-11-30','full_period_rows':len(full),'partial_december_rows':int(df.InvoiceDate.ge('2011-12-01').sum()),
 'retained_within_sheet_duplicate_rows':int(dups.sum()),'product_rows':len(product),
 'sale_rows':int((product.gross>0).sum()),'credit_rows':int((product.credit>0).sum()),
 'gross':gross,'credit':credit,'net':gross-credit,'credit_ratio_pct':credit/gross*100,
 'missing_customer_rows':int(unidentified.sum()),'missing_customer_gross':float(product.loc[unidentified,'gross'].sum()),
 'matched_credit':float(matched.matched_amount.sum()),'unmatched_credit':float(matched.unmatched_amount.sum()),'same_day_credit':float(matched.same_day_amount.sum()),
 'dedup_gross':float(dedup.gross.sum()),'dedup_credit':float(dedup.credit.sum()),'dedup_ratio_pct':float(dedup.credit.sum()/dedup.gross.sum()*100),
 'top5_credit_invoice_share_pct':float(invoice_credits.head(5).sum()/credit*100),
 'top10_product_credit_share_pct':float(sku.credit.head(10).sum()/credit*100),
 'quality':quality.to_dict('records'),
 'overseas_eligible':country_eligible.to_dict('records'),
 'top_products':sku.head(15).to_dict('records'),
 'largest_credit_lines':large[['Invoice','StockCode','Description','Country','InvoiceDate','credit','matched_amount','same_day_amount','unmatched_amount']].assign(InvoiceDate=lambda x:x.InvoiceDate.astype(str)).to_dict('records'),
 'top_country_products':country_sku.head(30).to_dict('records')
}
summary['france_focus']={
 'invoice':focus_id,'date':str(focus.InvoiceDate.min()),'credit':float(focus.credit.sum()),'lines':len(focus),'products':focus.StockCode.nunique(),
 'country_credit':float(fr.credit.sum()),'share_country_credit_pct':float(focus.credit.sum()/fr.credit.sum()*100),
 'country_ratio_without_focus_pct':float((fr.credit.sum()-focus.credit.sum())/fr.gross.sum()*100),
 'matched_amount':float(focus_matches.matched_amount.sum()),'same_day_amount':float(focus_matches.same_day_amount.sum()),
 'candidate_sales':candidate_invoices.assign(date=candidate_invoices.date.astype(str)).reset_index().to_dict('records'),
 'top_credit_invoices':fr_invoices.head(5).assign(date=lambda d:d.date.astype(str)).reset_index().to_dict('records')}
summary['january_extreme']={
 'invoice':'C541433','amount':77183.60,
 'share_january_credit_pct':77183.60/float(monthly.loc[monthly.month.eq('2011-01'),'credit'].iloc[0])*100,
 'ratio_without_pair_pct':(float(monthly.loc[monthly.month.eq('2011-01'),'credit'].iloc[0])-77183.60)/(float(monthly.loc[monthly.month.eq('2011-01'),'gross'].iloc[0])-77183.60)*100}
# All signed amounts are retained in the reconciliation, even when excluded from product KPIs.
assert len(full)==int(quality.rows.sum())
assert abs(full.amount.sum()-quality.signed_amount.sum())<1e-6
assert abs(gross-credit-product.amount.sum())<1e-6
assert abs(monthly.gross.sum()-gross)<1e-6 and abs(countries.credit.sum()-credit)<1e-6
assert abs(summary['matched_credit']+summary['unmatched_credit']-credit)<1e-6
assert 0<=summary['same_day_credit']<=summary['matched_credit']<=credit+1e-6
assert len(monthly)==24 and monthly.month.min()=='2009-12' and monthly.month.max()=='2011-11'
for name,table in [('monthly',monthly),('countries',countries),('products',sku),('country_products',country_sku),('quality',quality),('excluded_codes',nonproduct)]:
    table.to_csv(OUT/f'{name}.csv',index=False,float_format='%.6f')
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['top_country_products','top_products','largest_credit_lines']},ensure_ascii=False,indent=2))
print('TOP COUNTRY PRODUCTS\n',country_sku.head(20).to_string(index=False))
print('TOP CREDIT LINES\n',large[['Invoice','StockCode','Country','credit','matched_amount','same_day_amount']].to_string(index=False))
print('PASS: reconciliation, matching and 24-month coverage checks')

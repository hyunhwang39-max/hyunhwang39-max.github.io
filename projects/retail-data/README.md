# Online Retail II: sales and credit review

This directory contains aggregate outputs, not customer-level raw records.

Source: Chen, D. (2012), Online Retail II, UCI Machine Learning Repository.
https://doi.org/10.24432/C5CG6D — CC BY 4.0.
Downloaded 2026-11-14. Attribution and transformations are explained in
`../retail-analysis.html`.

Analysis window: 2009-12-01 through 2011-11-30. Currency: GBP.
The incomplete December 2011 is excluded. Cross-sheet copies are removed;
within-sheet identical rows remain in the baseline and are tested separately.
Product codes follow a documented pattern, not a supplied product master.

`gross`: positive recorded product sales, before credits.
`credit`: absolute amount of negative-quantity, positive-price product entries
whose invoice begins with C.
`credit_ratio_pct`: credit / gross × 100. This is not a cohort return rate.
`screened_ratio_pct`: same-day candidate credit amounts removed from the
numerator only, with the sales denominator unchanged. This is a sensitivity
view, not a corrected accounting figure.

Original-sale matching uses customer, country, product and price and allocates
available prior quantities newest-first. It is a candidate relationship,
not an explicit source-invoice link or evidence of a physical return.
Customer identifiers are not included in these exports.

To reproduce, place the official XLSX at `data/raw/online_retail_II.xlsx`, then:

```text
pip install -r scripts/requirements-retail.txt
python -m unittest discover -s scripts -p "test_retail*.py"
python scripts/analyze_retail.py
python scripts/plot_retail.py
python scripts/build_retail_report.py
python scripts/verify_retail_site.py
```

The analysis always reads the XLSX and fingerprints those same bytes; it does
not trust a cached pickle. Check `summary.json` for the source SHA-256.
No cost, margin, actual loss, cause of cancellation or realized improvement
can be established from these transaction fields alone.

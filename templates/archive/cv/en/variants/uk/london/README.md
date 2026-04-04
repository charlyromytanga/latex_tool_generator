# UK / London Application Pack

## CV versions

- `cv/cv_uk_london_bank.tex` : Investment Banks (Quant Dev / Risk / Model Validation)
- `cv/cv_uk_london_hedge_fund.tex` : Hedge Funds / Quant Funds (research-oriented)
- `cv/cv_uk_london_prop_hft.tex` : Prop Trading / HFT (performance + probability focus)

## Cover letter versions

- `lm/lm_uk_london_bank.tex`
- `lm/lm_uk_london_hedge_fund.tex`
- `lm/lm_uk_london_prop_hft.tex`

## Quick compile

From `uk/london`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error cv/cv_uk_london_bank.tex
pdflatex -interaction=nonstopmode -halt-on-error cv/cv_uk_london_hedge_fund.tex
pdflatex -interaction=nonstopmode -halt-on-error cv/cv_uk_london_prop_hft.tex

pdflatex -interaction=nonstopmode -halt-on-error lm/lm_uk_london_bank.tex
pdflatex -interaction=nonstopmode -halt-on-error lm/lm_uk_london_hedge_fund.tex
pdflatex -interaction=nonstopmode -halt-on-error lm/lm_uk_london_prop_hft.tex
```

## Customization

For each application, edit target company/role directly inside each `.tex` file before compiling.

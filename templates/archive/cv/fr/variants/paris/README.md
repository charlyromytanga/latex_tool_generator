# Pack Paris

## CV (1 page)
- `cv/cv_paris_consulting_quant_risk.tex`
- `cv/cv_paris_data_science_finance_regulation.tex`
- `cv/cv_paris_commodities_trading.tex`

## Lettres
- `lm/lm_paris_consulting_quant_risk.tex`
- `lm/lm_paris_data_science_finance_regulation.tex`
- `lm/lm_paris_commodities_trading.tex`

## Compilation
Depuis ce dossier:

```bash
pdflatex -interaction=nonstopmode -halt-on-error cv/cv_paris_consulting_quant_risk.tex
pdflatex -interaction=nonstopmode -halt-on-error cv/cv_paris_data_science_finance_regulation.tex
pdflatex -interaction=nonstopmode -halt-on-error cv/cv_paris_commodities_trading.tex

pdflatex -interaction=nonstopmode -halt-on-error lm/lm_paris_consulting_quant_risk.tex
pdflatex -interaction=nonstopmode -halt-on-error lm/lm_paris_data_science_finance_regulation.tex
pdflatex -interaction=nonstopmode -halt-on-error lm/lm_paris_commodities_trading.tex
```

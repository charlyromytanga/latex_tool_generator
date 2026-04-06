
# Image de base Python 3.12 avec LaTeX
FROM python:3.12-slim

# Installation de LaTeX et utilitaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    make latexmk texlive-xetex texlive-latex-extra texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*


# Définir le répertoire de travail
WORKDIR /app


# Par défaut, ouvrir un shell interactif
CMD ["/bin/bash"]

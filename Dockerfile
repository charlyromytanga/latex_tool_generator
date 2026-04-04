# Image de base complète et maintenue
FROM texlive/texlive:latest

# Installation de quelques utilitaires supplémentaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    make latexmk \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Par défaut, ouvrir un shell interactif
CMD ["/bin/bash"]

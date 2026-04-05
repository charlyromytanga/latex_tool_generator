#!/bin/bash
# Script local pour nettoyer les fichiers auxiliaires LaTeX côté hôte

# Dossiers locaux
SRC_DIR="./src"
OUTPUT_DIR="./output"

# Fichiers auxiliaires à supprimer dans src et output
files_to_delete="*.aux *.log *.out *.toc *.lof *.snm *.nav *.bcf *.run.xml *.bbl *.blg"

echo "Suppression des fichiers auxiliaires..."
find "$SRC_DIR" -type f \( -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.toc" -o -name "*.lof" -o -name "*.snm" -o -name "*.nav" -o -name "*.bcf" -o -name "*.run.xml" -o -name "*.bbl" -o -name "*.blg" \) -delete
find "$OUTPUT_DIR" -type f \( -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.toc" -o -name "*.lof" -o -name "*.snm" -o -name "*.nav" -o -name "*.bcf" -o -name "*.run.xml" -o -name "*.bbl" -o -name "*.blg" -o -name "*.gz" \) -delete

echo "Nettoyage terminé."

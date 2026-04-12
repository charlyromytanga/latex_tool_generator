"""
Script Python pour convertir un texte multi-ligne en chaîne JSON compatible (échappement des retours à la ligne et des guillemets).
Usage : python convert_multiline_to_json.py < fichier.txt
"""
import sys
import json

def multiline_to_json_string(text: str) -> str:
    # On utilise json.dumps pour échapper correctement tous les caractères
    return json.dumps(text)[1:-1]  # On retire les guillemets extérieurs

if __name__ == "__main__":
    # Lecture du texte depuis stdin ou d'un fichier
    if not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        print("Usage : python convert_multiline_to_json.py < fichier.txt")
        sys.exit(1)
    print(multiline_to_json_string(input_text))

"""
Module de stub pour l'analyse d'images (textures, screenshots) et appel API IA.
Ici on place des fonctions qui prépareront l'envoi à des APIs externes.
"""

import base64


def encode_image_bytes(image_bytes: bytes) -> str:
    """Retourne une chaîne base64 prête à être envoyée à une API."""
    return base64.b64encode(image_bytes).decode('utf-8')


def analyze_image_bytes(image_bytes: bytes, api_client=None):
    """Stub: analyse d'une image via un client API optionnel.
    - `api_client` peut être un wrapper utilisateur pour appeler des APIs externes.
    Retourne un dict de résultats simulés.
    """
    encoded = encode_image_bytes(image_bytes)
    # ici on appellerait api_client.analyze(encoded) si fourni
    result = {
        'width': None,
        'height': None,
        'issues': [],
        'ai_summary': None,
    }
    if api_client is not None:
        try:
            resp = api_client.analyze(encoded)
            result.update(resp)
        except Exception:
            pass
    return result


def register():
    pass


def unregister():
    pass

"""Wrapper minimal pour appeler l'API Generative Language (Gemini) via REST.

Ce module utilise urllib (pas de dépendances binaires) et lit la clé API
et le modèle depuis les préférences de l'addon :
- `T4A_AddonPreferences.google_api_key` -> API key
- `T4A_AddonPreferences.model_name` -> modèle (ex: "gemini-2.5-flash")

Il expose trois fonctions principales attendues par le reste de l'addon :
- `list_models(api_key=None)` : interroge l'endpoint models et met à jour `prefs.model_list_json`.
- `test_connection(api_key=None, model=None)` : envoie un ping simple.
- `analyze_text_dimensions(api_key=None, text, model=None)` : envoie le prompt d'analyse.

Le code se base sur le style REST simple de votre exemple (urllib.request).
"""

import time
import json
import logging
import traceback
import urllib.request
import urllib.error

import bpy

logger = logging.getLogger('T4A.Gemini')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)


def _get_prefs():
    try:
        pkg = __package__ or 'T4A_3DFilesQtCheck'
        return bpy.context.preferences.addons[pkg].preferences
    except Exception:
        return None


def _extract_text_from_response_obj(obj):
    """Récupère le texte depuis diverses formes de réponse JSON."""
    try:
        if not obj:
            return ''
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            # Try candidates / outputs / content blocks
            # Common shapes: {'candidates':[{'content':{'parts':[{'text':...}]}}]}
            if 'candidates' in obj and isinstance(obj['candidates'], list) and obj['candidates']:
                try:
                    c = obj['candidates'][0]
                    # nested content.parts
                    parts = c.get('content', {}).get('parts') if isinstance(c.get('content', {}), dict) else None
                    if parts and isinstance(parts, list) and parts[0].get('text'):
                        return parts[0].get('text')
                except Exception:
                    pass
            # older shapes
            for key in ('outputs', 'predictions'):
                v = obj.get(key)
                if isinstance(v, list) and v:
                    try:
                        first = v[0]
                        if isinstance(first, dict):
                            t = first.get('text') or first.get('content')
                            if isinstance(t, str):
                                return t
                    except Exception:
                        pass
            # fallback: find any 'text' string inside dict
            def walk(o):
                if o is None:
                    return None
                if isinstance(o, str):
                    return o
                if isinstance(o, dict):
                    for k, vv in o.items():
                        if k == 'text' and isinstance(vv, str):
                            return vv
                        res = walk(vv)
                        if res:
                            return res
                if isinstance(o, list):
                    for item in o:
                        res = walk(item)
                        if res:
                            return res
                return None

            found = walk(obj)
            return found or ''
        if isinstance(obj, list):
            for it in obj:
                s = _extract_text_from_response_obj(it)
                if s:
                    return s
        return ''
    except Exception:
        return ''


def _ensure_api_key_and_model(api_key: str = None, model: str = None):
    prefs = _get_prefs()
    if api_key:
        key = api_key
    else:
        key = ''
        try:
            if prefs is not None:
                key = (prefs.google_api_key or '').strip()
        except Exception:
            key = ''
    if model:
        m = model
    else:
        m = None
        try:
            if prefs is not None:
                m = getattr(prefs, 'model_name', None)
        except Exception:
            m = None
    return key, (m or '')


def call_gemini_api(prompt: str, api_key: str, model: str, timeout: int = 30):
    """Appel REST minimaliste basé sur votre exemple.

    Retourne la chaîne produite par le modèle ou None en cas d'échec.
    """
    try:
        if not api_key:
            return None
        model_id = (model or '').replace('models/', '').strip()
        if not model_id:
            return None

        # utilise v1beta generateContent path (v1/v1beta peuvent varier selon clé)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        data_bytes = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers)
        logger.debug('Envoi vers endpoint: %s', url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = resp.read().decode('utf-8')
            try:
                obj = json.loads(txt)
            except Exception:
                logger.debug('Réponse non JSON: %s', txt[:200])
                return None
            # extraire texte
            out = _extract_text_from_response_obj(obj)
            if out:
                return out
            # fallback: return full obj string
            return str(obj)
    except urllib.error.HTTPError as he:
        try:
            body = he.read().decode('utf-8')
        except Exception:
            body = ''
        logger.error('HTTPError %s: %s', he.code, body)
        return None
    except Exception:
        logger.error('Exception calling Gemini: %s', traceback.format_exc())
        return None


# Public API


def list_models(api_key: str = None) -> dict:
    """Récupère la liste des modèles via l'endpoint v1beta et met à jour prefs.model_list_json.

    Retourne dict {'success': bool, 'status_code': int|None, 'detail': data_or_msg}
    """
    key, _ = _ensure_api_key_and_model(api_key=api_key)
    if not key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    headers = {'Content-Type': 'application/json'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            txt = resp.read().decode('utf-8')
            try:
                obj = json.loads(txt)
            except Exception:
                return {'success': False, 'status_code': None, 'detail': 'Non-JSON response from models endpoint'}

            # extract short names
            names = []
            for m in obj.get('models', []) if isinstance(obj, dict) else []:
                try:
                    raw = m.get('name') if isinstance(m, dict) else str(m)
                    short = raw.split('/')[-1].strip()
                    if short and short not in names:
                        names.append(short)
                except Exception:
                    continue

            # store into prefs
            try:
                prefs = _get_prefs()
                if prefs is not None:
                    prefs.model_list_json = json.dumps(names)
                    prefs.model_list_ts = time.time()
            except Exception:
                logger.debug('Failed to save models into prefs: %s', traceback.format_exc())

            return {'success': True, 'status_code': 200, 'detail': names}
    except urllib.error.HTTPError as he:
        try:
            body = he.read().decode('utf-8')
        except Exception:
            body = ''
        logger.error('HTTPError listing models: %s %s', getattr(he, 'code', '?'), body)
        return {'success': False, 'status_code': getattr(he, 'code', None), 'detail': body}
    except Exception:
        tb = traceback.format_exc()
        logger.error('Exception listing models: %s', tb)
        return {'success': False, 'status_code': None, 'detail': tb}


def test_connection(api_key: str = None, model: str = None) -> dict:
    key, m = _ensure_api_key_and_model(api_key=api_key, model=model)
    if not key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}
    if not m:
        # attempt to pick first model from prefs
        try:
            prefs = _get_prefs()
            if prefs is not None:
                lst = json.loads(prefs.model_list_json or '[]')
                if lst:
                    m = lst[0]
        except Exception:
            m = m or ''
    # simple ping
    out = call_gemini_api('Ping: say hello briefly.', api_key=key, model=m)
    if out:
        return {'success': True, 'status_code': None, 'detail': out}
    return {'success': False, 'status_code': None, 'detail': 'No response from REST endpoint'}


def analyze_text_dimensions(api_key: str = None, text: str = '', model: str = None) -> dict:
    key, m = _ensure_api_key_and_model(api_key=api_key, model=model)
    if not key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}

    # ensure model list fresh: try to refresh synchronously if empty
    try:
        prefs = _get_prefs()
        if prefs is not None:
            try:
                current = json.loads(prefs.model_list_json or '[]')
            except Exception:
                current = []
            if not current:
                list_models(key)
    except Exception:
        pass

    if not m:
        try:
            if prefs is not None:
                m = getattr(prefs, 'model_name', '')
        except Exception:
            m = m or ''

    prompt_text = (
        "Extract the 3D model dimensions from the following text. "
        "Return the result as a compact string in meters in the format: "
        "width: <value> m; height: <value> m; depth: <value> m. "
        "If no dimensions are present, reply: NOT_FOUND. \nText:\n" + text
    )

    out = call_gemini_api(prompt_text, api_key=key, model=m, timeout=30)
    if out:
        return {'success': True, 'status_code': None, 'detail': out}
    else:
        return {'success': False, 'status_code': None, 'detail': 'REST generate failed: no response'}


__all__ = ('list_models', 'test_connection', 'analyze_text_dimensions', 'call_gemini_api')

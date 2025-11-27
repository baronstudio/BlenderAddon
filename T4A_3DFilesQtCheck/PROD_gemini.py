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
import traceback
import urllib.request
import urllib.error

import bpy


def _t4a_print(level: str, msg: str, *args):
    try:
        if args:
            print(f"[T4A] [{level}] " + (msg % args))
        else:
            print(f"[T4A] [{level}] {msg}")
    except Exception:
        if args:
            parts = ' '.join(str(a) for a in args)
            print(f"[T4A] [{level}] {msg} {parts}")
        else:
            print(f"[T4A] [{level}] {msg}")


class _SimpleLogger:
    def debug(self, msg, *args):
        # Only print debug messages if debug mode is enabled
        try:
            from . import PROD_Parameters
            if PROD_Parameters.is_debug_mode():
                _t4a_print('DEBUG', msg, *args)
        except Exception:
            pass

    def info(self, msg, *args):
        _t4a_print('INFO', msg, *args)

    def error(self, msg, *args):
        _t4a_print('ERROR', msg, *args)


logger = _SimpleLogger()


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

            # extract all models with compatibility info
            models_data = []
            seen_names = set()
            for m in obj.get('models', []) if isinstance(obj, dict) else []:
                try:
                    raw = m.get('name') if isinstance(m, dict) else str(m)
                    short = raw.split('/')[-1].strip()
                    if short and short not in seen_names:
                        seen_names.add(short)
                        # Check if model supports generateContent
                        supported_methods = m.get('supportedGenerationMethods', []) if isinstance(m, dict) else []
                        is_compatible = 'generateContent' in supported_methods
                        models_data.append({
                            'name': short,
                            'compatible': is_compatible
                        })
                except Exception:
                    continue

            # store into prefs
            try:
                prefs = _get_prefs()
                if prefs is not None:
                    prefs.model_list_json = json.dumps(models_data)
                    prefs.model_list_ts = time.time()
            except Exception:
                logger.debug('Failed to save models into prefs: %s', traceback.format_exc())

            return {'success': True, 'status_code': 200, 'detail': models_data}
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


def test_connection(api_key: str = None, model: str = None, context=None) -> dict:
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
    
    # Utiliser le système de prompts configurables
    try:
        from . import PROD_prompt_tags
        ping_prompt = PROD_prompt_tags.get_connection_test_prompt(context)
    except Exception:
        # Fallback vers l'ancien prompt
        ping_prompt = 'Ping: say hello briefly.'
    
    out = call_gemini_api(ping_prompt, api_key=key, model=m)
    if out:
        return {'success': True, 'status_code': None, 'detail': out}
    return {'success': False, 'status_code': None, 'detail': 'No response from REST endpoint'}


def analyze_text_dimensions(api_key: str = None, text: str = '', model: str = None, context=None, file_path: str = '') -> dict:
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

    # Utiliser le système de prompts configurables
    try:
        from . import PROD_prompt_tags
        prompt_text = PROD_prompt_tags.get_text_analysis_prompt(text, file_path, context)
    except Exception:
        # Fallback vers l'ancien prompt
        prompt_text = (
            "Extract the 3D model dimensions from the following text. "
            "Return the result as a compact string in meters in the format: "
            "width: <value> m; height: <value> m; depth: <value> m. "
            "If no dimensions are present, reply: NOT_FOUND. \nText:\n" + text
        )

    # Get timeout from preferences
    timeout = 30
    try:
        prefs = _get_prefs()
        if prefs:
            timeout = getattr(prefs, 'api_timeout', 30)
    except Exception:
        pass

    out = call_gemini_api(prompt_text, api_key=key, model=m, timeout=timeout)
    if out:
        return {'success': True, 'status_code': None, 'detail': out}
    else:
        return {'success': False, 'status_code': None, 'detail': 'REST generate failed: no response'}


def analyze_image_with_ocr(api_key=None, image_path=None, model=None, context=None, timeout=None, use_text_prompt=False):
    """Analyze an image file with Gemini Vision, focusing on OCR and technical content extraction.
    
    Args:
        api_key: Google API key for Gemini
        image_path: Path to the image file (JPG/PNG)
        model: Model name to use (defaults to prefs)
        context: Blender context (optional)
        timeout: Request timeout in seconds (defaults to prefs)
        use_text_prompt: If True, use text analysis prompt instead of image prompt
        
    Returns:
        Dict with 'success', 'status_code', 'detail' keys
    """
    import base64
    import os
    
    if not image_path or not os.path.exists(image_path):
        return {'success': False, 'status_code': None, 'detail': 'Image file not found'}
    
    # Read and encode image
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        return {'success': False, 'status_code': None, 'detail': f'Failed to read image: {e}'}
    
    # Determine MIME type
    ext = os.path.splitext(image_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        mime_type = 'image/jpeg'
    elif ext == '.png':
        mime_type = 'image/png'
    else:
        return {'success': False, 'status_code': None, 'detail': f'Unsupported image format: {ext}'}
    
    # Get API key and model
    key = api_key
    m = model
    prefs = None
    
    try:
        from . import PROD_Parameters
        prefs = PROD_Parameters.get_addon_preferences()
    except Exception:
        pass
    
    if not key and prefs:
        try:
            key = getattr(prefs, 'google_api_key', '')
        except Exception:
            pass
    
    if not m and prefs:
        try:
            m = getattr(prefs, 'model_name', '')
        except Exception:
            pass
    
    if not key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}
    
    if not m:
        m = 'gemini-2.5-flash'  # default model with vision support
    
    # Get timeout from preferences if not provided
    if timeout is None:
        timeout = 30
        try:
            if prefs:
                timeout = getattr(prefs, 'api_timeout', 30)
        except Exception:
            pass
    
    # Utiliser le système de prompts configurables
    try:
        from . import PROD_prompt_tags
        if use_text_prompt:
            # Utiliser le prompt d'analyse de texte pour extraire les dimensions
            prompt_text = PROD_prompt_tags.get_text_analysis_prompt(
                text_content="",  # Pas de texte, l'image sera analysée
                file_path=image_path, 
                context=context,
                content_type="image"
            )
        else:
            # Utiliser le prompt spécialisé pour l'analyse d'image
            prompt_text = PROD_prompt_tags.get_image_analysis_prompt(image_path, context)
    except Exception:
        # Fallback vers l'ancien prompt
        if use_text_prompt:
            file_name = os.path.basename(image_path) if image_path else "unknown"
            prompt_text = f"""Extract the 3D model dimensions from this image. Return the result as a compact string in meters in the format: width: <value> m; height: <value> m; depth: <value> m. If no dimensions are present, reply: NOT_FOUND.
Image file: {file_name}
Analyze the image for dimensional information."""
        else:
            prompt_text = f"""Analyze this image thoroughly for 3D modeling and quality control:
Image: {os.path.basename(image_path)}
Extract dimensions, text, and technical information."""

    # Call Gemini API with image
    out = call_gemini_api(prompt_text, api_key=key, model=m, timeout=timeout, image_data=image_b64, image_mime_type=mime_type)
    if out:
        return {'success': True, 'status_code': None, 'detail': out}
    else:
        return {'success': False, 'status_code': None, 'detail': 'REST generate with image failed: no response'}


def call_gemini_api(prompt, api_key=None, model=None, timeout=30, image_data=None, image_mime_type=None):
    """Enhanced version of call_gemini_api that supports image input.
    
    Args:
        prompt: Text prompt
        api_key: Google API key
        model: Model name
        timeout: Request timeout
        image_data: Base64-encoded image data (optional)
        image_mime_type: MIME type of image (optional, e.g. 'image/jpeg')
        
    Returns:
        Response text or None on failure
    """
    key, m = _ensure_api_key_and_model(api_key=api_key, model=model)
    if not key:
        logger.error('No API key provided for Gemini call')
        return None
    if not m:
        m = 'gemini-2.5-flash'  # fallback

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
    
    # Build request payload
    try:
        if image_data and image_mime_type:
            # Multi-modal request with image
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": image_mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }]
            }
        else:
            # Text-only request
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
        
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=req_data, 
            headers={'Content-Type': 'application/json'}
        )
        
        logger.debug('Calling Gemini API: %s', url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            response_data = resp.read().decode('utf-8')
            
        response_json = json.loads(response_data)
        
        # Extract text from response
        try:
            candidates = response_json.get('candidates', [])
            if candidates and len(candidates) > 0:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts and len(parts) > 0:
                    return parts[0].get('text', '')
        except Exception as e:
            logger.error('Error parsing Gemini response: %s', e)
            logger.debug('Raw response: %s', response_data)
            
        return None
        
    except urllib.error.HTTPError as he:
        try:
            error_body = he.read().decode('utf-8')
            logger.error('Gemini API HTTP error %s: %s', he.code, error_body)
        except Exception:
            logger.error('Gemini API HTTP error: %s', he.code)
        return None
    except Exception as e:
        logger.error('Gemini API call failed: %s', e)
        return None


__all__ = ('list_models', 'test_connection', 'analyze_text_dimensions', 'analyze_image_with_ocr', 'call_gemini_api')

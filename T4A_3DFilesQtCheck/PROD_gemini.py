"""Module to interact with Google Generative AI (Gemini) for dimension inference.

This file provides a small `test_connection` function that attempts to contact
Google's Generative AI endpoint using the provided API key and a tiny prompt.

Implementation notes:
- Uses `requests` if available; otherwise falls back to `urllib.request`.
- Does NOT store API keys; caller should provide key from secure source.
- The endpoint and exact payload may need adjustments depending on the exact
  Google API version and deployment (here we use a conservative REST POST
  to a hypothetical `generate` endpoint for `gemini_flash_2.0`).

Security:
- Do not commit API keys. Prefer storing them in the Add-on preferences or
  environment variables and avoid printing them to logs.
"""

import json
import logging
import traceback
import time

try:
    import google.generativeai as genai
    _GENAI = True
except Exception:
    genai = None
    _GENAI = False

try:
    import requests
except Exception:
    requests = None


# Logger for this module
logger = logging.getLogger('T4A.Gemini')
if not logger.handlers:
    # Avoid configuring root logger; add a simple handler to ensure messages appear
    handler = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def _redact_key(key: str) -> str:
    if not key:
        return '<none>'
    try:
        k = str(key)
        if len(k) <= 10:
            return '<redacted>'
        return k[:6] + '...' + k[-4:]
    except Exception:
        return '<redacted>'


# Old Vertex/service-account flow removed. Use google-generativeai + API key.


def _safe_truncate(obj, length=800):
    try:
        s = str(obj)
    except Exception:
        return '<unrepresentable>'
    if len(s) > length:
        return s[:length] + '...'
    return s


def test_connection(api_key: str, model: str = 'models/gemini-2.5-flash-lite') -> dict:
    """Test connection to the Generative AI model.

    Returns a dict with keys: success (bool), status_code (int|None), detail (str).
    """
    if not api_key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}

    if not _GENAI:
        return {'success': False, 'status_code': None, 'detail': 'google-generativeai not installed; run dependency installer'}

    # Configure library with the provided API key
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        tb = traceback.format_exc()
        return {'success': False, 'status_code': None, 'detail': f'Failed to configure google-generativeai: {tb}'}

    # quick ping to model
    prompt = 'Ping: say hello briefly.'
    attempts = 3
    backoff = 0.5
    for i in range(attempts):
        try:
            model_obj = genai.GenerativeModel(model)
            resp = model_obj.generate_content(prompt)
            # library exposes text on response in many versions
            text = getattr(resp, 'text', None) or str(resp)
            return {'success': True, 'status_code': None, 'detail': text}
        except Exception as e:
            last = traceback.format_exc()
            time.sleep(backoff)
            backoff *= 2
            continue
    return {'success': False, 'status_code': None, 'detail': 'Test failed after retries: ' + last}


__all__ = (
    'test_connection',
    'analyze_text_dimensions',
    'list_models',
)


def analyze_text_dimensions(api_key: str, text: str, model: str = 'models/gemini-2.5-flash-lite') -> dict:
    """Send text to Gemini to extract dimensions.

    Returns a dict: {'success': bool, 'status_code': int|None, 'detail': str}
    where 'detail' is the model's raw text response or parsed JSON.
    This function logs request/response snippets and returns tracebacks on error
    to help debugging in environments where exceptions were previously silenced.
    """
    if not api_key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}

    if not _GENAI:
        return {'success': False, 'status_code': None, 'detail': 'google-generativeai not installed; run dependency installer'}

    prompt_text = (
        "Extract the 3D model dimensions from the following text. "
        "Return the result as a compact string in meters in the format: "
        "width: <value> m; height: <value> m; depth: <value> m. "
        "If no dimensions are present, reply: NOT_FOUND. \nText:\n" + text
    )

    # configure
    try:
        genai.configure(api_key=api_key)
    except Exception:
        return {'success': False, 'status_code': None, 'detail': 'Failed to configure google-generativeai library'}

    attempts = 3
    backoff = 0.5
    last = None
    for i in range(attempts):
        try:
            model_obj = genai.GenerativeModel(model)
            resp = model_obj.generate_content(prompt_text)
            text_resp = getattr(resp, 'text', None) or str(resp)
            return {'success': True, 'status_code': None, 'detail': text_resp}
        except Exception:
            last = traceback.format_exc()
            time.sleep(backoff)
            backoff *= 2
            continue
    return {'success': False, 'status_code': None, 'detail': 'Analyze failed after retries: ' + (last or '')}


def list_models(api_key: str) -> dict:
    """List available models.
        Parameters:
            - api_key: API key or bearer token.
    """
    if not api_key:
        return {'success': False, 'status_code': None, 'detail': 'No API key provided'}

    # prefer using google-generativeai if available
    if _GENAI:
        try:
            # genai may not provide a direct list_models helper; try introspection
            genai.configure(api_key=api_key)
            try:
                models = genai.list_models()
                return {'success': True, 'status_code': None, 'detail': models}
            except Exception:
                # fallback to REST call below
                pass
        except Exception:
            pass

    # fallback: call public Generative Language models list via REST using API key
    if requests is None:
        return {'success': False, 'status_code': None, 'detail': 'requests not installed; run dependency installer.'}

    url = 'https://generativelanguage.googleapis.com/v1/models'
    if str(api_key).startswith('AIza'):
        url = url + f'?key={api_key}'
        headers = {'Content-Type': 'application/json'}
    else:
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}

    attempts = 3
    backoff = 0.5
    for i in range(attempts):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            try:
                data = resp.json()
            except Exception:
                data = {'text': resp.text}
            return {'success': resp.status_code == 200, 'status_code': resp.status_code, 'detail': data}
        except Exception:
            time.sleep(backoff)
            backoff *= 2
            continue
    tb = traceback.format_exc()
    return {'success': False, 'status_code': None, 'detail': tb}

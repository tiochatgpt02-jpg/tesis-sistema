"""Single server-side gateway for educational text generation."""
import json
import socket
import urllib.error
import urllib.request

from config import Config


class GenerationError(RuntimeError):
    pass


def provider_status():
    provider = Config.AI_PROVIDER
    key = Config.GROQ_API_KEY if provider == 'groq' else Config.NVIDIA_API_KEY
    model = Config.GROQ_MODEL if provider == 'groq' else Config.NVIDIA_MODEL
    configured = provider in {'groq', 'nvidia'} and bool(key)
    return {'provider': provider, 'model': model, 'configured': configured,
            'running': configured, 'model_available': configured,
            'verification': 'configuration_only'}


def generate_text(prompt, timeout=None, json_mode=False):
    # The student request path must work even when the external API is down.
    from flask import has_request_context, request as flask_request
    if has_request_context() and flask_request.path.startswith('/student'):
        raise GenerationError('El alumno usa contenido preparado; no se genera IA durante su respuesta.')
    provider = Config.AI_PROVIDER
    if provider == 'groq':
        endpoint = 'https://api.groq.com/openai/v1/chat/completions'
        key, model = Config.GROQ_API_KEY, Config.GROQ_MODEL
    elif provider == 'nvidia':
        endpoint = 'https://integrate.api.nvidia.com/v1/chat/completions'
        key, model = Config.NVIDIA_API_KEY, Config.NVIDIA_MODEL
    else:
        raise GenerationError('Proveedor de IA no configurado: usa groq o nvidia.')
    if not key:
        raise GenerationError(f'Falta configurar la clave de {provider} en el servidor.')
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': str(prompt)}],
        'temperature': 0.1,
        'max_tokens': Config.AI_MAX_OUTPUT_TOKENS,
        'stream': False,
    }
    if provider == 'groq' and 'gpt-oss' in model:
        payload['reasoning_effort'] = 'low'
    if json_mode:
        payload['response_format'] = {'type': 'json_object'}
    request = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}',
                 'User-Agent': 'AulaComputacionTesis/1.0'},
        method='POST',
    )
    wait = min(float(timeout or Config.AI_TIMEOUT_SECONDS), Config.AI_TIMEOUT_SECONDS)
    try:
        with urllib.request.urlopen(request, timeout=wait) as response:
            data = json.loads(response.read(2_000_000).decode('utf-8'))
        choice = data['choices'][0]
        content = choice['message']['content']
        if choice.get('finish_reason') == 'length':
            raise GenerationError('La respuesta de IA excedió el límite; reduce el material o las preguntas.')
        if not isinstance(content, str) or not content.strip():
            raise GenerationError('El proveedor devolvió una respuesta vacía.')
        return content.strip()
    except urllib.error.HTTPError as exc:
        # Never expose provider response bodies, prompts or authorization headers.
        if exc.code == 429:
            raise GenerationError('Cuota de IA agotada temporalmente. Los contenidos publicados siguen disponibles.') from None
        raise GenerationError(f'El proveedor de IA no pudo completar la solicitud (HTTP {exc.code}).') from None
    except (TimeoutError, socket.timeout):
        raise GenerationError('La IA no respondió a tiempo. Inténtalo de nuevo desde el panel docente.') from None
    except urllib.error.URLError:
        raise GenerationError('No se pudo conectar con el proveedor de IA. Comprueba la conexión del servidor.') from None
    except (KeyError, IndexError, TypeError, ValueError):
        raise GenerationError('El proveedor devolvió una respuesta no válida.') from None

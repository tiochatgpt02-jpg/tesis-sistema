import os
from pathlib import Path

from flask import current_app, send_from_directory
from services.file_storage_service import store_bytes, read_bytes, delete_bytes


def save_presentation_file(uploaded_file, filename):
    storage_dir = Path(current_app.instance_path) / 'uploads' / 'presentations'
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_file = storage_dir / filename
    uploaded_file.save(stored_file)
    store_bytes(f'presentations/{filename}', stored_file.read_bytes())
    return f'presentations/{filename}', stored_file.stat().st_size


def resolve_presentation_path(file_path):
    stored_path = str(file_path or '').replace('\\', '/').lstrip('/')
    if stored_path.startswith('static/'):
        root = Path(current_app.root_path).resolve()
        target = (root / stored_path).resolve()
    elif stored_path.startswith('presentations/'):
        root = (Path(current_app.instance_path) / 'uploads').resolve()
        target = (root / stored_path).resolve()
    else:
        raise FileNotFoundError('La ruta almacenada para la presentación no es válida')
    if os.path.commonpath((str(root), str(target))) != str(root):
        raise FileNotFoundError('La ruta almacenada para la presentación no es válida')
    if not target.is_file():
        content = read_bytes(stored_path)
        if content is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    return target


def send_presentation_file(file_path, download_name, as_attachment=False):
    resolve_presentation_path(file_path)
    stored_path = str(file_path or '').replace('\\', '/').lstrip('/')
    if stored_path.startswith('static/'):
        return send_from_directory(
            current_app.root_path,
            stored_path,
            as_attachment=as_attachment,
            download_name=download_name,
        )
    if stored_path.startswith('presentations/'):
        return send_from_directory(
            Path(current_app.instance_path) / 'uploads',
            stored_path,
            as_attachment=as_attachment,
            download_name=download_name,
        )
    raise FileNotFoundError('La ruta almacenada para la presentación no es válida')


def delete_stored_presentation_file(file_path):
    delete_bytes(str(file_path or '').replace('\\', '/').lstrip('/'))
    try:
        path = resolve_presentation_path(file_path)
    except FileNotFoundError:
        return
    if path.is_file():
        os.remove(path)

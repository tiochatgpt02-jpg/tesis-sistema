import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Dict, Any, List, Optional
from flask import current_app
from services.presentation_storage import resolve_presentation_path


class MaterialExtractorService:
    """
    Servicio de extracción de contenido educativo a partir de materiales del profesor:
    - Presentaciones PPTX (títulos de diapositivas, viñetas, notas del orador)
    - Texto plano / lecciones
    - Interfaz preparada para documentos PDF
    """

    XML_NAMESPACES = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    }

    @classmethod
    def extract_from_pptx(cls, file_path: str) -> Dict[str, Any]:
        """
        Extrae texto estructurado de una presentación PPTX utilizando zipfile y XML nativo.
        No requiere dependencias externas pesadas.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        if not zipfile.is_zipfile(file_path):
            # Fallback en caso de que sea un archivo de texto con extensión cambiada
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return cls.extract_from_text(content, title=os.path.basename(file_path))
            except Exception as exc:
                raise ValueError(f"El archivo {file_path} no es un formato PPTX válido: {exc}")

        slide_titles: List[str] = []
        key_points: List[str] = []
        all_text_blocks: List[str] = []
        speaker_notes: List[str] = []

        with zipfile.ZipFile(file_path, 'r') as zf:
            file_names = zf.namelist()
            
            # 1. Diapositivas ordenadas numéricamente
            slide_files = [f for f in file_names if re.match(r'^ppt/slides/slide\d+\.xml$', f)]
            slide_files.sort(key=lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 0)

            for slide_file in slide_files:
                try:
                    xml_content = zf.read(slide_file)
                    root = ET.fromstring(xml_content)
                    
                    slide_extracted_title = ""
                    slide_body_points = []

                    # Buscar formas que contengan texto
                    for sp in root.findall('.//p:sp', cls.XML_NAMESPACES):
                        # Verificar si es título
                        is_title = False
                        ph = sp.find('.//p:ph', cls.XML_NAMESPACES)
                        if ph is not None:
                            ph_type = ph.attrib.get('type', '')
                            if ph_type in ('title', 'ctrTitle', 'subTitle', '') or not ph_type:
                                if ph_type in ('title', 'ctrTitle') or not slide_extracted_title:
                                    is_title = True

                        c_nv_pr = sp.find('.//p:cNvPr', cls.XML_NAMESPACES)
                        if c_nv_pr is not None:
                            name_val = c_nv_pr.attrib.get('name', '').lower()
                            if 'title' in name_val:
                                is_title = True

                        # Extraer párrafos de texto
                        for p in sp.findall('.//a:p', cls.XML_NAMESPACES):
                            texts = [t.text for t in p.findall('.//a:t', cls.XML_NAMESPACES) if t.text]
                            line = ''.join(texts).strip()
                            if not line:
                                continue

                            if is_title and not slide_extracted_title:
                                slide_extracted_title = line
                            else:
                                slide_body_points.append(line)

                    # Fallback si no hubo placeholder de título explícito: primer texto de la diapositiva
                    if not slide_extracted_title and slide_body_points:
                        slide_extracted_title = slide_body_points.pop(0)

                    if slide_extracted_title:
                        slide_titles.append(slide_extracted_title)
                        all_text_blocks.append(f"# {slide_extracted_title}")

                    for pt in slide_body_points:
                        key_points.append(pt)
                        all_text_blocks.append(f"- {pt}")

                except Exception:
                    continue

            # 2. Notas del orador (ppt/notesSlides/notesSlide*.xml)
            note_files = [f for f in file_names if re.match(r'^ppt/notesSlides/notesSlide\d+\.xml$', f)]
            for note_file in note_files:
                try:
                    note_xml = zf.read(note_file)
                    note_root = ET.fromstring(note_xml)
                    for p in note_root.findall('.//a:p', cls.XML_NAMESPACES):
                        texts = [t.text for t in p.findall('.//a:t', cls.XML_NAMESPACES) if t.text]
                        line = ''.join(texts).strip()
                        if line and len(line) > 10 and not re.match(r'^\d+$', line):
                            speaker_notes.append(line)
                except Exception:
                    continue

        raw_text_combined = "\n".join(all_text_blocks)
        # En los PPT del profesor la portada puede titularse solo con el grado
        # (por ejemplo, "4° SEC.") y el tema real aparece como "TEMA: ...".
        # Priorizar ese marcador evita mandar un grado como si fuese la materia.
        topic_match = re.search(
            r'\btema\w*\s*:\s*([^\n#]+)', raw_text_combined, re.IGNORECASE,
        )
        declared_topic = topic_match.group(1).strip(' -•\t') if topic_match else ''
        main_title = declared_topic or (slide_titles[0] if slide_titles else os.path.splitext(os.path.basename(file_path))[0])
        # Limpiar y filtrar puntos clave únicos
        unique_points = []
        seen = set()
        for pt in key_points:
            cleaned = pt.strip()
            if len(cleaned) > 5 and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                unique_points.append(cleaned)

        if speaker_notes:
            raw_text_combined += "\n\nNotas del orador:\n" + "\n".join(f"* {n}" for n in speaker_notes[:5])

        raw_text = raw_text_combined.strip() or f"Presentación sobre {main_title}"
        return {
            "source_type": "pptx",
            "title": main_title,
            "key_points": unique_points[:15],
            "raw_text": raw_text,
            "slides_count": len(slide_files),
            "speaker_notes_count": len(speaker_notes),
            "image_count": len([name for name in file_names if name.startswith('ppt/media/')]),
            "learning_summary": cls._build_learning_summary(main_title, unique_points, raw_text),
        }

    @classmethod
    def extract_from_docx(cls, file_path: str) -> Dict[str, Any]:
        """Extrae párrafos de un DOCX sin depender de conversores externos."""
        if not os.path.exists(file_path) or not zipfile.is_zipfile(file_path):
            raise ValueError('El archivo DOCX no es válido.')

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                document_xml = ET.fromstring(zf.read('word/document.xml'))
        except (KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
            raise ValueError('No se pudo leer el contenido del archivo DOCX.') from exc

        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = []
        for paragraph in document_xml.findall('.//w:p', ns):
            text = ''.join(node.text or '' for node in paragraph.findall('.//w:t', ns)).strip()
            if text:
                paragraphs.append(text)

        content = '\n'.join(paragraphs).strip()
        if not content:
            raise ValueError('El DOCX no contiene texto legible.')
        title = os.path.splitext(os.path.basename(file_path))[0].replace('_', ' ').replace('-', ' ').title()
        extracted = cls.extract_from_text(content, title=title)
        extracted['source_type'] = 'docx'
        return extracted

    @classmethod
    def extract_from_text(cls, text: str, title: str = "") -> Dict[str, Any]:
        """
        Extrae puntos clave y estructura de un texto educativo plano o markdown.
        """
        clean_text = (text or "").strip()
        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]

        derived_title = title.strip()
        if not derived_title and lines:
            first_line = re.sub(r'^[#*\-\s]+', '', lines[0]).strip()
            derived_title = first_line[:60] if first_line else "Material Educativo"

        key_points: List[str] = []
        for line in lines:
            # Detectar viñetas o frases informativas
            stripped = re.sub(r'^[#*\-\d\.\)\s]+', '', line).strip()
            if len(stripped) >= 15 and not stripped.endswith(':'):
                key_points.append(stripped)

        # Si hay pocas viñetas, extraer oraciones delimitadas por punto
        if len(key_points) < 3:
            sentences = [s.strip() for s in re.split(r'[.;]\s*', clean_text) if len(s.strip()) >= 15]
            for s in sentences:
                if s not in key_points:
                    key_points.append(s)

        # De-duplicar
        unique_points = []
        seen = set()
        for pt in key_points:
            if pt.lower() not in seen:
                seen.add(pt.lower())
                unique_points.append(pt)

        return {
            "source_type": "text",
            "title": derived_title or "Material Educativo",
            "key_points": unique_points[:12],
            "raw_text": clean_text,
            "slides_count": 0,
            "speaker_notes_count": 0,
            "image_count": 0,
            "learning_summary": cls._build_learning_summary(derived_title or "Material Educativo", unique_points, clean_text),
        }

    @classmethod
    def extract_from_pdf(cls, file_path: str) -> Dict[str, Any]:
        """
        Interfaz extensible para lectura de texto en documentos PDF.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        extracted_text = ""
        # Intentar pypdf / pdfminer si estuvieran disponibles
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                extracted_text += (page.extract_text() or '') + "\n"
        except ImportError:
            # Fallback lector básico de cadenas legibles en PDF
            try:
                with open(file_path, 'rb') as f:
                    raw_bytes = f.read()
                # Extraer bloques de texto en streams
                text_chunks = re.findall(rb'\(([^)]+)\)', raw_bytes)
                if text_chunks:
                    extracted_text = ' '.join(c.decode('utf-8', errors='ignore') for c in text_chunks if len(c) > 3)
            except Exception:
                extracted_text = ""

        if not extracted_text.strip():
            raise ValueError('No se pudo extraer texto del PDF. Usa un PDF con texto seleccionable o un DOCX/PPTX; los documentos escaneados requieren OCR.')

        filename_title = os.path.splitext(os.path.basename(file_path))[0].replace('_', ' ').replace('-', ' ').title()
        res = cls.extract_from_text(extracted_text, title=filename_title)
        res["source_type"] = "pdf"
        return res

    @classmethod
    def extract_from_source(cls, source_type: str, file_path_or_text: str, title: str = "") -> Dict[str, Any]:
        """
        Método centralizador para extraer contenido según el tipo de fuente.
        """
        stype = (source_type or "").lower().strip()
        if stype in ('pptx', 'ppt', 'presentacion'):
            return cls.extract_from_pptx(file_path_or_text)
        elif stype == 'docx':
            return cls.extract_from_docx(file_path_or_text)
        elif stype in ('pdf', 'documento'):
            return cls.extract_from_pdf(file_path_or_text)
        else:
            return cls.extract_from_text(file_path_or_text, title=title)

    @classmethod
    def extract_from_presentation_record(cls, presentation: Dict[str, Any], require_content: bool = True) -> Dict[str, Any]:
        """Lee el archivo PPT asociado al registro y falla si el archivo no aporta contenido."""
        absolute_path = str(resolve_presentation_path(presentation.get('file_path')))
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        upload_root = os.path.abspath(os.path.join(current_app.instance_path, 'uploads'))
        try:
            inside_project = os.path.commonpath([project_root, absolute_path]) == project_root
            inside_uploads = os.path.commonpath([upload_root, absolute_path]) == upload_root
        except ValueError:
            inside_project = False
            inside_uploads = False

        if not (inside_project or inside_uploads) or not os.path.isfile(absolute_path):
            raise FileNotFoundError('No se encontró el archivo de la presentación.')

        extension = os.path.splitext(absolute_path)[1].lower()
        if not zipfile.is_zipfile(absolute_path) and extension != '.txt':
            raise ValueError('El archivo de la presentación no es un PPTX legible.')

        extracted = cls.extract_from_source(
            source_type=extension.lstrip('.') or 'pptx',
            file_path_or_text=absolute_path,
            title=presentation.get('title') or 'Presentación de Clase',
        )
        raw_text = (extracted.get('raw_text') or '').strip()
        title = (extracted.get('title') or presentation.get('title') or '').strip()
        if require_content and (not raw_text or len(raw_text) < max(25, len(title) + 12)):
            raise ValueError('La presentación no contiene suficiente texto para crear preguntas.')
        return extracted

    @staticmethod
    def _build_learning_summary(title: str, key_points: List[str], raw_text: str) -> Dict[str, Any]:
        """Resumen interno y auditable para el prompt; no agrega conocimiento externo."""
        stop_words = {
            'para', 'como', 'este', 'esta', 'estos', 'estas', 'desde', 'sobre', 'entre',
            'mediante', 'también', 'porque', 'donde', 'cada', 'todos', 'todas', 'según',
            'material', 'profesor', 'clase', 'tema', 'educativo', 'aprende', 'aprender',
        }
        words = re.findall(r'\b[a-záéíóúüñ]{4,}\b', (raw_text or '').lower())
        keywords = [word for word, _ in Counter(word for word in words if word not in stop_words).most_common(10)]
        examples = [point for point in key_points if re.search(r'\b(ejemplo|por ejemplo|como)\b', point, re.IGNORECASE)]
        return {
            'topic': title,
            'concepts': key_points[:8],
            'keywords': keywords,
            'examples': (examples or key_points[:3])[:3],
            'level': 'primaria',
        }

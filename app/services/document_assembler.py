import logging
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any
from tempfile import NamedTemporaryFile

import requests
from docx import Document
from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx2pdf import convert as docx_to_pdf

from app.services.docx_core import ensure_project_dir, save_json
from app.services.gost_applier import apply_gost_formatting
from app.services.title_page_generator import generate_title_page
from app.services.styles import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


SECTION_ORDER = ['introduction', 'theory', 'practice', 'conclusion']
SECTION_TITLES = {
    'introduction': 'Введение',
    'theory': 'Теоретическая часть',
    'practice': 'Практическая часть',
    'conclusion': 'Заключение',
}

SECTION_PATTERNS = [
    ('introduction', 'введение'),
    ('introduction', 'цель работы'),
    ('introduction', 'цель лабораторной работы'),
    ('theory', 'теоретическая часть'),
    ('theory', 'теоретические сведения'),
    ('theory', 'теория'),
    ('practice', 'практическая часть'),
    ('practice', 'ход работы'),
    ('practice', 'выполнение работы'),
    ('practice', 'экспериментальная часть'),
    ('practice', 'задание'),
    ('conclusion', 'заключение'),
    ('conclusion', 'выводы'),
    ('conclusion', 'вывод'),
]


def _detect_section(text: str) -> str | None:
    text_lower = str(text or '').lower().strip()
    for section_key, keyword in SECTION_PATTERNS:
        if keyword in text_lower:
            return section_key
    return None


def _is_section_header(text: str) -> bool:
    text = str(text or '').strip()
    if not text:
        return False
    if len(text) > 120:
        return False
    return _detect_section(text) is not None


def _paragraph_text(para: Any) -> str:
    if isinstance(para, dict):
        return str(para.get('text', '') or '')
    return str(para or '')


def _paragraph_index(para: Any, fallback: int) -> int:
    if isinstance(para, dict):
        value = para.get('index')
        try:
            return int(value)
        except Exception:
            return fallback
    return fallback


def _image_paragraph_position(image: dict) -> int | None:
    for key in ('insert_before_paragraph', 'paragraph_index', 'position'):
        value = image.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except Exception:
            continue
    return None


def _is_user_image(image: dict) -> bool:
    return str(image.get('source') or '').lower() == 'user_uploaded_image'


def apply_ml_changes_to_structure(
    original_structure: Dict[str, Any],
    ml_response: Dict[str, Any]
) -> Dict[str, Any]:
    logger.info("=" * 50)
    logger.info("Applying ML changes to structure")

    result = {
        'paragraphs': original_structure.get('paragraphs', []),
        'tables': original_structure.get('tables', []),
        'images': original_structure.get('images', []),
        'content_blocks': original_structure.get('content_blocks', []),
    }

    # Обогащаем картинки из DOCX данными ML: caption/type/insert/ocr_text.
    ml_images = ml_response.get('images') or []
    if ml_images:
        logger.info(f"Found ML images: {len(ml_images)}")
        by_id = {
            item.get('image_id') or item.get('id'): item
            for item in ml_images
            if item.get('image_id') or item.get('id')
        }
        merged_images = []
        for original_img in result['images']:
            image_id = original_img.get('id') or original_img.get('image_id')
            ml_img = by_id.get(image_id, {})
            merged = {
                **original_img,
                **ml_img,
                'local_path': original_img.get('local_path') or original_img.get('path'),
                'source': original_img.get('source') or ml_img.get('source') or 'original_docx_image',
            }
            merged_images.append(merged)
        result['images'] = merged_images

    uploaded_images = ml_response.get('uploaded_images') or []
    if uploaded_images:
        logger.info(f"Found uploaded_images: {len(uploaded_images)}")
        normalized_uploaded = []
        for idx, img in enumerate(uploaded_images, start=1):
            if not isinstance(img, dict):
                continue

            image_id = img.get('image_id') or img.get('id') or f'user_image_{idx}'
            normalized_uploaded.append({
                **img,
                'id': image_id,
                'image_id': image_id,
                'source': 'user_uploaded_image',
                'insert_strategy': img.get('insert_strategy') or 'after_practice',
                # local_path для user image не используем приоритетно: он относится к Backend №1, а не к Doc Service.
                'caption': img.get('caption') or img.get('generated_caption') or '',
            })
        result['images'].extend(normalized_uploaded)

    original_sections = extract_sections_from_paragraphs(result['paragraphs'])
    generated_sections = []

    if 'generated_sections' in ml_response:
        generated_sections = ml_response['generated_sections']
        logger.info(f"Found 'generated_sections' at root: {len(generated_sections)} sections")
    elif 'report' in ml_response and 'generated_sections' in ml_response['report']:
        generated_sections = ml_response['report']['generated_sections']
        logger.info(f"Found 'generated_sections' in 'report': {len(generated_sections)} sections")
    else:
        logger.warning("No 'generated_sections' found in ml_response")

    ml_sections_keys = set()
    for section in generated_sections:
        section_key = section.get('section')
        section_text = section.get('text', '')
        section_title = section.get('title', '')

        logger.debug(f"Processing section: {section_key}")
        logger.debug(f"  Title: {section_title[:50]}...")
        logger.debug(f"  Text length: {len(section_text)} chars")

        if section_key:
            result[section_key] = {
                'type': 'section',
                'title': section_title or SECTION_TITLES.get(section_key, section_key),
                'content': section_text,
                'source': 'ml'
            }
            ml_sections_keys.add(section_key)
            logger.info(f"ML replaced section: {section_key}")

    for section_key in SECTION_ORDER:
        if section_key not in ml_sections_keys:
            original_content = original_sections.get(section_key, '')
            if original_content:
                result[section_key] = {
                    'type': 'section',
                    'title': SECTION_TITLES.get(section_key, section_key),
                    'content': original_content,
                    'source': 'original'
                }
                logger.info(f"Kept original section: {section_key} ({len(original_content)} chars)")
            else:
                logger.debug(f"No original content for section: {section_key}")

    bibliography = []
    if 'bibliography' in ml_response:
        bibliography = ml_response['bibliography']
        logger.info(f"Found 'bibliography' at root: {len(bibliography)} items")
    elif 'report' in ml_response and 'bibliography' in ml_response['report']:
        bibliography = ml_response['report']['bibliography']
        logger.info(f"Found 'bibliography' in 'report': {len(bibliography)} items")

    if bibliography:
        result['bibliography'] = bibliography
        for i, ref in enumerate(bibliography):
            logger.debug(f"  Bibliography {i + 1}: {str(ref)[:50]}...")

    logger.info(f"Final result keys: {list(result.keys())}")
    logger.info("=" * 50)
    return result


def extract_sections_from_paragraphs(paragraphs: list) -> Dict[str, str]:
    sections = {key: '' for key in SECTION_ORDER}
    current_section = None

    for pos, para in enumerate(paragraphs):
        text = _paragraph_text(para)
        if not text.strip():
            continue

        if _is_section_header(text):
            detected = _detect_section(text)
            if detected:
                current_section = detected
                logger.debug(f"Section header detected: '{text[:50]}...' -> {current_section}")
            continue

        if current_section and text.strip():
            sections[current_section] += ('\n' if sections[current_section] else '') + text

    for key, value in sections.items():
        logger.debug(f"Section '{key}': {len(value)} chars" if value else f"Section '{key}': empty")
    return sections


def _build_section_ranges(paragraphs: list) -> dict[str, list[int]]:
    """
    Возвращает индексы исходных paragraph'ов, которые относятся к каждой секции.
    Это нужно, чтобы картинки из DOCX вставлялись не пачкой в конец, а рядом с исходным контекстом.
    """
    ranges: dict[str, list[int]] = {key: [] for key in SECTION_ORDER}
    current_section = None

    for pos, para in enumerate(paragraphs):
        text = _paragraph_text(para)
        paragraph_idx = _paragraph_index(para, pos)

        if not text.strip():
            continue

        if _is_section_header(text):
            detected = _detect_section(text)
            if detected:
                current_section = detected
                ranges.setdefault(current_section, [])
            continue

        if current_section:
            ranges.setdefault(current_section, []).append(paragraph_idx)

    logger.info(
        "Section paragraph ranges: "
        + ", ".join(f"{key}={values[:1]}..{values[-1:] if values else []}" for key, values in ranges.items())
    )
    return ranges


def _detect_image_section(image: dict, section_ranges: dict[str, list[int]]) -> str:
    if _is_user_image(image):
        return 'practice'

    pos = _image_paragraph_position(image)
    if pos is None:
        return 'practice'

    for section_key in SECTION_ORDER:
        indices = section_ranges.get(section_key) or []
        if not indices:
            continue
        if min(indices) <= pos <= max(indices):
            return section_key

    # Если картинка стоит после последнего практического абзаца, но до вывода — это всё равно практика.
    practice_indices = section_ranges.get('practice') or []
    conclusion_indices = section_ranges.get('conclusion') or []
    if practice_indices and conclusion_indices:
        if max(practice_indices) <= pos <= min(conclusion_indices):
            return 'practice'

    return 'practice'


def _image_slot_inside_section(image: dict, section_key: str, section_ranges: dict[str, list[int]], content_paragraphs_count: int) -> int:
    """
    Переводит insert_before_paragraph из исходного документа в приблизительное место внутри
    нового текста секции, который мог быть заменён ML.
    """
    if content_paragraphs_count <= 0:
        return 0

    if _is_user_image(image):
        return content_paragraphs_count

    pos = _image_paragraph_position(image)
    indices = section_ranges.get(section_key) or []

    if pos is None or not indices:
        return content_paragraphs_count

    start = min(indices)
    end = max(indices)

    if end <= start:
        return min(content_paragraphs_count, 1)

    ratio = (pos - start) / max(1, end - start + 1)
    slot = round(ratio * content_paragraphs_count)
    return max(0, min(content_paragraphs_count, slot))


def _prepare_images_by_section(structure: Dict[str, Any], section_ranges: dict[str, list[int]]) -> dict[str, list[dict]]:
    images_by_section: dict[str, list[dict]] = {key: [] for key in SECTION_ORDER}

    for image in structure.get('images', []) or []:
        if not isinstance(image, dict):
            continue

        section_key = _detect_image_section(image, section_ranges)
        image['_resolved_section'] = section_key
        images_by_section.setdefault(section_key, []).append(image)

    for section_key, images in images_by_section.items():
        images.sort(key=lambda item: (_image_paragraph_position(item) is None, _image_paragraph_position(item) or 10**9))
        if images:
            logger.info(f"Images assigned to section '{section_key}': {len(images)}")

    return images_by_section


def _download_image_to_temp(url: str) -> str | None:
    """
    Скачивает внешнюю картинку во временный файл.
    Нужно для user_uploaded_image, потому что они физически лежат в Backend №1,
    а итоговый DOCX собирает Doc Service.
    """
    try:
        logger.info(f"Downloading external image for DOCX insert: {url}")

        response = requests.get(
            url,
            timeout=(5, 30),
            headers={"User-Agent": "DocService/1.0"},
        )

        logger.info(f"External image download status={response.status_code}")
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        suffix = '.png'
        if 'jpeg' in content_type or 'jpg' in content_type:
            suffix = '.jpg'
        elif 'webp' in content_type:
            suffix = '.webp'
        elif 'gif' in content_type:
            suffix = '.gif'
        elif 'png' in content_type:
            suffix = '.png'

        tmp = NamedTemporaryFile(delete=False, suffix=suffix, prefix='doc_service_external_image_')
        with tmp:
            tmp.write(response.content)

        logger.info(f"External image saved to temp file: {tmp.name}")
        return tmp.name

    except Exception as exc:
        logger.warning(f"Could not download image from URL: {url}; error={exc}")
        return None


def _pick_raw_image_path(image: dict) -> str:
    """
    Для картинок из DOCX сначала используем local_path, потому что они лежат у Doc Service.
    Для картинок пользователя сначала используем URL path, потому что они лежат у Backend №1.
    """
    if _is_user_image(image):
        return str(image.get('path') or image.get('url') or image.get('local_path') or '')

    return str(image.get('local_path') or image.get('path') or image.get('url') or '')


def _resolve_image_for_docx(image: dict) -> tuple[Path | None, str | None]:
    raw_path = _pick_raw_image_path(image)

    if not raw_path:
        return None, None

    if raw_path.startswith('http://') or raw_path.startswith('https://'):
        downloaded = _download_image_to_temp(raw_path)
        if downloaded:
            return Path(downloaded), downloaded
        return None, None

    path = Path(raw_path.replace('\\', '/'))

    if path.exists():
        return path, None

    logger.warning(f"Image file not found, skipping: {path}")
    return None, None


def _clean_caption_text(text: str) -> str:
    text = str(text or '').strip()
    if not text:
        return ''

    bad_fragments = [
        'image', '.png', '.jpg', '.jpeg', '.webp', '.gif',
        'иллюстрация к отчёту', 'пользовательское изображение',
        'screenshot', 'снимок экрана', 'unknown', 'none',
    ]

    lower = text.lower()
    if any(fragment in lower for fragment in bad_fragments):
        return ''

    if lower.startswith('рисунок'):
        parts = text.split('—', 1)
        if len(parts) == 2 and parts[1].strip():
            return parts[1].strip()
        return ''

    return text


def _caption_from_ocr(image: dict) -> str:
    ocr = str(image.get('ocr_text') or image.get('text') or '').lower()

    if not ocr:
        return ''

    if 'bubble_sort' in ocr or 'пузыр' in ocr:
        return 'Фрагмент программной реализации пузырьковой сортировки'

    if 'python' in ocr and ('sort' in ocr or 'сорт' in ocr):
        return 'Фрагмент программного кода для сравнения алгоритмов сортировки'

    if 'o(n log n)' in ocr or 'n log n' in ocr:
        return 'Сравнение алгоритмов по асимптотической сложности'

    if 'o(n2)' in ocr or 'o(n^2)' in ocr or 'o(n²)' in ocr or 'квадрат' in ocr:
        return 'Пример квадратичной временной сложности алгоритма'

    if 'figure' in ocr or 'график' in ocr or 'время' in ocr and 'n' in ocr:
        return 'График зависимости времени выполнения от размера входных данных'

    if 'класс' in ocr and 'название' in ocr:
        return 'Классификация основных классов асимптотической сложности'

    return ''


def _human_caption_by_type(image: dict, index: int) -> str:
    """
    Нормальная индивидуальная подпись без имени файла.
    Приоритет: caption от ML -> OCR keywords -> тип изображения -> source.
    """
    source = str(image.get('source') or '').lower()
    img_type = str(
        image.get('type')
        or image.get('image_type')
        or image.get('classification')
        or ''
    ).lower()

    raw_caption = _clean_caption_text(
        image.get('caption')
        or image.get('generated_caption')
        or image.get('description')
        or ''
    )

    if raw_caption:
        return f"Рисунок {index} — {raw_caption}"

    ocr_caption = _caption_from_ocr(image)
    if ocr_caption:
        return f"Рисунок {index} — {ocr_caption}"

    if source == 'user_uploaded_image':
        return f"Рисунок {index} — Дополнительный материал, загруженный пользователем"

    if 'graph' in img_type or 'chart' in img_type or 'граф' in img_type:
        return f"Рисунок {index} — График зависимости времени выполнения от размера входных данных"

    if 'table' in img_type or 'табл' in img_type:
        return f"Рисунок {index} — Таблица результатов анализа алгоритмов"

    if 'scheme' in img_type or 'diagram' in img_type or 'схем' in img_type:
        return f"Рисунок {index} — Схема выполнения алгоритма"

    if 'formula' in img_type or 'формул' in img_type:
        return f"Рисунок {index} — Формулы асимптотической оценки сложности"

    if 'code' in img_type or 'screenshot' in img_type or 'скрин' in img_type:
        return f"Рисунок {index} — Фрагмент программной реализации"

    # Подписи по порядку для типовой лабораторной по асимптотике.
    default_by_position = {
        1: 'Классификация основных классов асимптотической сложности',
        2: 'Результат выполнения задания по классификации сложности',
        3: 'Фрагмент программной реализации расчёта сложности циклов',
        4: 'Пример записи асимптотических оценок',
        5: 'Программная реализация эксперимента с пузырьковой сортировкой',
        6: 'График зависимости времени выполнения от размера входных данных',
        7: 'Фрагмент кода сравнения пузырьковой и встроенной сортировки',
        8: 'График сравнения времени выполнения алгоритмов сортировки',
        9: 'Дополнительные вычисления асимптотических оценок',
    }
    if index in default_by_position:
        return f"Рисунок {index} — {default_by_position[index]}"

    return f"Рисунок {index} — Материал к выполнению лабораторной работы"


def _insert_single_image(doc: Document, image: dict, image_number: int, temp_files: list[str]) -> bool:
    path, temp_file = _resolve_image_for_docx(image)

    if temp_file:
        temp_files.append(temp_file)

    if not path or not path.exists():
        logger.warning(f"Image {image_number} cannot be resolved, skipping")
        return False

    try:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run = paragraph.add_run()
        run.add_picture(str(path), width=Cm(12))

        caption_text = _human_caption_by_type(image, image_number)

        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run(caption_text)
        caption_run.italic = True

        logger.info(f"Added image {image_number}: {path}")
        logger.info(f"Image {image_number} caption: {caption_text}")
        return True

    except Exception as exc:
        logger.error(f"Failed to add image {image_number}: {path}; error={exc}")
        return False


def _insert_images_for_slot(
    doc: Document,
    images: list[dict],
    image_counter: int,
    temp_files: list[str],
    section_key: str,
    slot: int,
) -> int:
    for image in images:
        logger.info(
            f"Placing image #{image_counter} in section '{section_key}', slot={slot}, "
            f"source={image.get('source')}, insert_before_paragraph={image.get('insert_before_paragraph')}"
        )
        if _insert_single_image(doc, image, image_counter, temp_files):
            image_counter += 1
    return image_counter


def build_document_from_structured_data(structure: Dict[str, Any], output_path: str) -> str:
    logger.info("=" * 50)
    logger.info("BUILDING DOCUMENT FROM STRUCTURE")
    logger.debug(f"Structure keys: {list(structure.keys())}")

    doc = Document()
    doc = setup_document_styles(doc)

    paragraphs = structure.get('paragraphs', []) or []
    section_ranges = _build_section_ranges(paragraphs)
    images_by_section = _prepare_images_by_section(structure, section_ranges)

    added_count = 0
    image_counter = 1
    temp_files: list[str] = []

    try:
        for section_key in SECTION_ORDER:
            section = structure.get(section_key)
            if section and isinstance(section, dict):
                title = section.get('title', SECTION_TITLES.get(section_key, section_key))
                content = section.get('content', '')
                content_paragraphs = [p.strip() for p in str(content).split('\n') if p.strip()]

                if content_paragraphs:
                    add_heading_center(doc, title)

                    section_images = images_by_section.get(section_key, []) or []
                    slots: dict[int, list[dict]] = {}
                    for image in section_images:
                        slot = _image_slot_inside_section(
                            image=image,
                            section_key=section_key,
                            section_ranges=section_ranges,
                            content_paragraphs_count=len(content_paragraphs),
                        )
                        slots.setdefault(slot, []).append(image)

                    # Вставляем картинки до/между абзацами секции по рассчитанным slot.
                    for para_index in range(len(content_paragraphs) + 1):
                        if para_index in slots:
                            image_counter = _insert_images_for_slot(
                                doc=doc,
                                images=slots[para_index],
                                image_counter=image_counter,
                                temp_files=temp_files,
                                section_key=section_key,
                                slot=para_index,
                            )

                        if para_index < len(content_paragraphs):
                            add_gost_paragraph(doc, content_paragraphs[para_index])

                    added_count += 1
                    logger.info(
                        f"Added section '{section_key}' with {len(content)} chars and {len(section_images)} images"
                    )
                else:
                    logger.warning(f"Section '{section_key}' has empty content, skipping")
            else:
                logger.debug(f"Section '{section_key}' not found or not a dict")

        logger.info(f"Total sections added: {added_count}")

        # Если какие-то картинки не попали в известные секции, добавляем их перед библиографией.
        already_known = set()
        for images in images_by_section.values():
            already_known.update(id(img) for img in images)

        leftover_images = [
            img for img in structure.get('images', []) or []
            if isinstance(img, dict) and id(img) not in already_known
        ]
        if leftover_images:
            add_heading_center(doc, 'Иллюстративные материалы')
            image_counter = _insert_images_for_slot(
                doc=doc,
                images=leftover_images,
                image_counter=image_counter,
                temp_files=temp_files,
                section_key='materials',
                slot=0,
            )

        bibliography = structure.get('bibliography', [])
        if bibliography:
            add_heading_center(doc, 'Список литературы')
            for i, ref in enumerate(bibliography):
                add_bibliography_item(doc, i + 1, ref)
                logger.debug(f"  Bibliography item {i + 1}: {str(ref)[:50]}...")
            logger.info(f"Added bibliography with {len(bibliography)} items")
        else:
            logger.debug('No bibliography found in structure')

        doc.save(output_path)
        logger.info(f"Document saved successfully to: {output_path}")
        logger.debug(f"Output file size: {Path(output_path).stat().st_size} bytes")

    except Exception as e:
        logger.error(f"Failed to save/build document: {str(e)}")
        raise

    finally:
        for filename in temp_files:
            try:
                Path(filename).unlink(missing_ok=True)
                logger.debug(f"Removed temp image file: {filename}")
            except Exception as exc:
                logger.warning(f"Could not remove temp image file: {filename}; error={exc}")

    logger.info("=" * 50)
    return output_path


def assemble_full_document(
    project_id: str,
    ml_response: Dict[str, Any],
    title_page_data: Dict[str, Any],
    output_filename: str = None
) -> Dict[str, Any]:
    logger.info("=" * 50)
    logger.info(f"Starting full document assembly for project: {project_id}")

    project_dir = ensure_project_dir(project_id)
    extracted_path = project_dir / 'extract_response.json'
    if not extracted_path.exists():
        error_msg = f'Extracted data not found for project {project_id} at {extracted_path}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}

    logger.debug(f"Loading extracted structure from: {extracted_path}")
    with open(extracted_path, 'r', encoding='utf-8') as f:
        original_structure = json.load(f)

    logger.debug(
        f"Original structure has {len(original_structure.get('paragraphs', []))} paragraphs, "
        f"{len(original_structure.get('images', []))} images"
    )

    merged_structure = apply_ml_changes_to_structure(original_structure, ml_response)

    merged_path = project_dir / 'merged_structure.json'
    save_json(merged_path, merged_structure)
    logger.debug(f"Merged structure saved to: {merged_path}")

    if output_filename:
        if output_filename.endswith('.docx'):
            temp_docx = project_dir / output_filename.replace('_final.docx', '_temp.docx')
            gost_docx = project_dir / output_filename.replace('_final.docx', '_gost.docx')
            final_docx = project_dir / output_filename
        else:
            temp_docx = project_dir / f'{output_filename}_temp.docx'
            gost_docx = project_dir / f'{output_filename}_gost.docx'
            final_docx = project_dir / f'{output_filename}.docx'
    else:
        temp_docx = project_dir / f'{project_id}_temp.docx'
        gost_docx = project_dir / f'{project_id}_gost.docx'
        final_docx = project_dir / f'{project_id}_final.docx'

    logger.debug(f"Temp file: {temp_docx}")
    logger.debug(f"GOST file: {gost_docx}")
    logger.debug(f"Final file: {final_docx}")

    logger.info('Building temporary document...')
    build_document_from_structured_data(merged_structure, str(temp_docx))
    if not temp_docx.exists():
        return {'status': 'failed', 'error': f'Temp file not created: {temp_docx}'}
    logger.info(f"Temp file created: {temp_docx.stat().st_size} bytes")

    logger.info('Applying GOST formatting...')
    apply_gost_formatting(str(temp_docx), str(gost_docx))
    if not gost_docx.exists():
        return {'status': 'failed', 'error': f'GOST file not created: {gost_docx}'}
    logger.info(f"GOST file created: {gost_docx.stat().st_size} bytes")

    logger.info('Adding title page...')
    generate_title_page(
        input_path=str(gost_docx),
        output_path=str(final_docx),
        department=title_page_data.get('department', ''),
        discipline=title_page_data.get('discipline', ''),
        lab_number=title_page_data.get('lab_number', ''),
        lab_title=title_page_data.get('lab_title', ''),
        student_name=title_page_data.get('student_name', ''),
        student_group=title_page_data.get('student_group', ''),
        reviewer_name=title_page_data.get('reviewer_name', ''),
    )

    if not final_docx.exists():
        return {'status': 'failed', 'error': f'Final file not created: {final_docx}'}

    logger.info(f"Final file created: {final_docx.stat().st_size} bytes")
    temp_docx.unlink(missing_ok=True)
    gost_docx.unlink(missing_ok=True)
    logger.debug('Temporary files cleaned up')
    logger.info(f"Assembly completed successfully for project {project_id}")
    logger.info("=" * 50)
    return {'status': 'completed', 'output_path': str(final_docx), 'project_id': project_id}


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Конвертация DOCX в PDF.
    Сначала пытаемся через LibreOffice, затем fallback на docx2pdf/Word COM.
    """
    docx_path_obj = Path(docx_path).resolve()
    pdf_path_obj = Path(pdf_path).resolve()
    output_dir = pdf_path_obj.parent

    soffice_path = shutil.which('soffice')
    if not soffice_path:
        for possible in [
            r'C:\Program Files\LibreOffice\program\soffice.exe',
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
        ]:
            if Path(possible).exists():
                soffice_path = possible
                break

    if soffice_path:
        try:
            logger.info(f"Converting DOCX to PDF with LibreOffice: {docx_path_obj} -> {pdf_path_obj}")
            command = [
                soffice_path,
                '--headless',
                '--convert-to',
                'pdf',
                '--outdir',
                str(output_dir),
                str(docx_path_obj),
            ]
            logger.info(f"LibreOffice command: {' '.join(command)}")
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            logger.info(f"LibreOffice stdout: {result.stdout}")
            logger.info(f"LibreOffice stderr: {result.stderr}")
            logger.info(f"LibreOffice return code: {result.returncode}")

            generated_pdf = output_dir / f'{docx_path_obj.stem}.pdf'
            if generated_pdf.exists():
                if generated_pdf != pdf_path_obj:
                    generated_pdf.replace(pdf_path_obj)
                logger.info(f"PDF created successfully: {pdf_path_obj} ({pdf_path_obj.stat().st_size} bytes)")
                return True
        except Exception as exc:
            logger.error(f"LibreOffice PDF conversion failed: {exc}")

    try:
        logger.info(f"Converting DOCX to PDF with docx2pdf fallback: {docx_path} -> {pdf_path}")
        docx_to_pdf(docx_path, pdf_path)
        if Path(pdf_path).exists():
            logger.info(f"PDF created successfully: {pdf_path} ({Path(pdf_path).stat().st_size} bytes)")
            return True
        logger.error(f"PDF file not created: {pdf_path}")
        return False
    except Exception as e:
        logger.error(f"Failed to convert DOCX to PDF: {str(e)}")
        return False

from __future__ import annotations

from uuid import uuid4

from app.core.storage import create_document_record, load_state, save_export, save_state
from app.engine.analyzer import analyze_document
from app.engine.fix_engine import apply_fix_to_doc, inverse_fix
from app.parser.docx_loader import load_docx


def create_and_analyze(source_path: str) -> dict:
    document_id, working_path = create_document_record(source_path)
    result = analyze_document(str(working_path))
    fixes_map = {item['fix_id']: item for item in result['fixes']}

    state = load_state(document_id)
    state['issues'] = result['issues']
    state['fixes'] = fixes_map
    state['last_analysis'] = result['document_model']
    save_state(document_id, state)

    return {
        'document_id': document_id,
        'summary': {
            'issues_total': len(result['issues']),
            'auto_fixable': sum(1 for i in result['issues'] if i.get('can_auto_apply')),
        },
        'issues': result['issues'],
    }


def apply_fix(document_id: str, fix_id: str) -> dict:
    state = load_state(document_id)
    fix = state['fixes'].get(fix_id)
    if not fix:
        raise ValueError(f'Fix {fix_id} not found')

    working_path = state['working_path']
    doc = load_docx(working_path)
    doc = apply_fix_to_doc(doc, fix)
    doc.save(working_path)

    state['history'].append({
        'operation_id': uuid4().hex,
        'fix_id': fix_id,
        'status': 'applied',
        'inverse_fix': inverse_fix(fix),
    })
    save_state(document_id, state)

    return {
        'document_id': document_id,
        'fix_id': fix_id,
        'status': 'applied',
    }


def undo_last(document_id: str) -> dict:
    state = load_state(document_id)
    if not state['history']:
        return {
            'document_id': document_id,
            'status': 'nothing_to_undo',
        }

    last_record = state['history'].pop()
    inverse = last_record['inverse_fix']
    working_path = state['working_path']
    doc = load_docx(working_path)
    doc = apply_fix_to_doc(doc, inverse)
    doc.save(working_path)
    save_state(document_id, state)

    return {
        'document_id': document_id,
        'status': 'reverted',
        'fix_id': last_record['fix_id'],
    }


def get_issues(document_id: str) -> dict:
    state = load_state(document_id)
    return {
        'document_id': document_id,
        'issues': state['issues'],
    }


def export_document(document_id: str) -> str:
    state = load_state(document_id)
    export_path = save_export(document_id, state['working_path'])
    return str(export_path)

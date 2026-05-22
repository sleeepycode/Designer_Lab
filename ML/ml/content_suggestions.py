from ml.ai_generation import generate_missing_section, generate_bibliography

def build_content_suggestions(structure: dict, topic: str, document_text: str) -> tuple[list[dict], list[str], list[dict], bool]:
    generated_sections=[]; bibliography=[]; suggestions=[]; ai_used=False
    for section in structure.get('missing_sections',[]):
        if section=='references':
            bibliography,used=generate_bibliography(topic,document_text); ai_used=ai_used or used
            suggestions.append({'type':'missing_references','target':'references','action':'generate','title':'Список литературы','items':bibliography,'message':'В отчёте отсутствует список литературы. Можно добавить предложенные источники.'})
            continue
        generated,used=generate_missing_section(section,topic,document_text); ai_used=ai_used or used
        generated_sections.append(generated)
        suggestions.append({'type':'missing_section','target':section,'action':'generate','title':generated['title'],'text':generated['text'],'message':f'В отчёте отсутствует раздел «{generated["title"]}». Можно добавить сгенерированный текст.'})
    return generated_sections,bibliography,suggestions,ai_used

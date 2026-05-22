def apply_numbering(images: list[dict]) -> list[dict]:
    fig=1; tab=1; out=[]
    for item in images:
        cap=item.get('caption','Иллюстрация к отчёту')
        if item.get('type')=='table':
            item['number']=tab; item['numbering_type']='table'; item['caption']=f'Таблица {tab} — {strip_prefix(cap)}'; tab+=1
        else:
            item['number']=fig; item['numbering_type']='figure'; item['caption']=f'Рисунок {fig} — {strip_prefix(cap)}'; fig+=1
        out.append(item)
    return out
def strip_prefix(caption: str) -> str:
    return caption.split('—',1)[1].strip() if '—' in caption else caption.strip()

from docx import Document

def expand_paragraphs(doc):
    """جلب كل الفقرات بما في ذلك الموجودة داخل الجداول."""
    for p in doc.paragraphs:
        yield p
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p

def safe_replace_in_paragraph(paragraph, placeholders):
    """استبدال النصوص مع الحفاظ التام على التنسيق والخط العربي."""
    for key, val in placeholders.items():
        if key not in paragraph.text:
            continue
            
        # 1. محاولة الاستبدال المباشر داخل أجزاء النص (Runs)
        for run in paragraph.runs:
            if key in run.text:
                run.text = run.text.replace(key, str(val))
        
        # 2. حل مشكلة تقطيع الكلمات في وورد (إذا كانت الكلمة مقسمة بين كذا Run)
        if key in paragraph.text and len(paragraph.runs) > 0:
            full_text = "".join(r.text for r in paragraph.runs)
            paragraph.runs[0].text = full_text.replace(key, str(val))
            for i in range(1, len(paragraph.runs)):
                paragraph.runs[i].text = ""

def safe_replace_in_doc(doc, placeholders):
    """تطبيق الاستبدال على كامل المستند."""
    for p in expand_paragraphs(doc):
        safe_replace_in_paragraph(p, placeholders)

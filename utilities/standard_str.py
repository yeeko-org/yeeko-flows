
def standard(text: str) -> str:
    import unidecode
    import re
    if not text:
        return ""
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.strip()

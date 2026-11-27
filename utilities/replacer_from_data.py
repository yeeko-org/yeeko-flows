import re

PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def replace_parameter(extra_values_data: dict, text: str, default: str = ""):
    def resolve(key: str) -> str:
        if key not in extra_values_data:
            return default
        value = extra_values_data[key]
        # Un extra guardado vacío llega como None: imprimirlo sería «None».
        if value is None:
            return ""
        # re.sub exige str: los extras pueden ser lista (json, p. ej.
        # dias_laborables) o int (monto_pago); se coaccionan a texto.
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        return str(value)

    # Un renglón cuyos {{var}} quedan todos vacíos se omite entero, con su
    # salto: si no, queda la etiqueta suelta («El trabajo empezó el»). Un
    # renglón sin variables nunca se toca, así que `\n\n` sobrevive; solo si
    # el omitido estaba entre dos renglones en blanco se queda uno.
    lines: list[str] = []
    dropped = False
    for line in text.split("\n"):
        keys = PLACEHOLDER.findall(line)
        if keys and not any(resolve(key).strip() for key in keys):
            dropped = True
            continue
        if dropped and not line.strip() and lines and not lines[-1].strip():
            continue
        dropped = False
        lines.append(PLACEHOLDER.sub(lambda m: resolve(m.group(1)), line))
    result = "\n".join(lines)

    # `[^\S\n]` colapsa espacios/tabs horizontales (p. ej. el hueco que deja
    # un {{var}} vacío) pero conserva `\n`: WhatsApp los renderiza como salto
    # de línea y el viejo `\s+` los destruía (mensajes salían en un renglón).
    return re.sub(r'[^\S\n]+', ' ', result.strip())

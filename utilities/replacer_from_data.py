import re


def replace_parameter(extra_values_data: dict, text: str, default: str = ""):
    pattern = r"\{\{(\w+)\}\}"

    def replace_match(match):
        key = match.group(1)
        if key not in extra_values_data:
            return default
        value = extra_values_data[key]
        # re.sub exige str: los extras pueden ser lista (json, p. ej.
        # dias_laborables) o int (monto_pago); se coaccionan a texto.
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        return str(value)

    result = re.sub(pattern, replace_match, text)

    return re.sub(r'\s+', ' ', result.strip())

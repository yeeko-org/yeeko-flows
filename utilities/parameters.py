from django.db.models import QuerySet
from infrastructure.assign.models import ParamValue


TRUE_TEXTS = ("true", "1", "yes", "si", "sí")
FALSE_TEXTS = ("false", "0", "no")


def typed_value(value, data_type: str):
    """`ParamValue.value` is a string column: a `boolean` or `integer`
    parameter is handed over as a real bool or int. Every other type, and a
    text that does not parse, travels as stored."""
    if not isinstance(value, str):
        return value
    text = value.strip().lower()
    if data_type == "boolean":
        if text in TRUE_TEXTS:
            return True
        if text in FALSE_TEXTS:
            return False
    elif data_type == "integer":
        try:
            return int(text)
        except ValueError:
            pass
    return value


def update_parameters(
    query_param_value: QuerySet[ParamValue],
    parameters_dict: dict = {}
) -> dict:
    local_parameters = parameters_dict.copy()
    rows = query_param_value.values(
        "parameter__name", "parameter__data_type", "value")
    for param_value in rows:
        param_name = param_value["parameter__name"]
        local_parameters[param_name] = typed_value(
            param_value["value"], param_value["parameter__data_type"])

    return local_parameters


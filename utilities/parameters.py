import re

from django.db.models import QuerySet
from infrastructure.assign.models import ParamValue


def update_parameters(
    query_param_value: QuerySet[ParamValue],
    parameters_dict: dict = {}
) -> dict:
    local_parameters = parameters_dict.copy()
    for param_value in query_param_value.values("parameter__name", "value"):
        param_name = param_value["parameter__name"]
        local_parameters[param_name] = param_value["value"]

    return local_parameters


def replace_parameter(parameters_dict: dict, text: str, default: str = ""):
    pattern = r"\{\{(\w+)\}\}"

    def replace_match(match):
        key = match.group(1)
        if key in parameters_dict:
            return parameters_dict[key]
        else:
            return default

    result = re.sub(pattern, replace_match, text)

    # Gemela de replacer_from_data: `[^\S\n]` colapsa espacios horizontales
    # pero conserva `\n`, para no aplanar los saltos que van al mensaje final.
    return re.sub(r'[^\S\n]+', ' ', result.strip())

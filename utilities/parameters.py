import re

from django.db.models import QuerySet
from infrastructure.assign.models import ParamValue


def update_parameters(
    query_param_value: QuerySet[ParamValue],
    parameters_dict: dict = None
) -> dict:
    if parameters_dict is None:
        parameters_dict = {}
    local_parameters = parameters_dict.copy()
    for param_value in query_param_value.values("parameter__name", "value"):
        param_name = param_value["parameter__name"]
        local_parameters[param_name] = param_value["value"]

    return local_parameters


def replace_parameter(extra_values_data: dict, text: str, default: str = ""):
    # TODO Check together: Qué pasa con las variables con puntos?
    pattern = r"\{\{(\w+)\}\}"

    def replace_match(match):
        key = match.group(1)
        if key in extra_values_data:
            return extra_values_data[key]
        else:
            return default

    # TODO Lucian: No estamos contemplando si llega un JSON en
    #  el valor de la variable
    result = re.sub(pattern, replace_match, text)

    result_text = re.sub(r'\s+', ' ', result.strip())

    print("--------------------")
    print("extra_values_data: ", extra_values_data)
    print("text: ", text)
    print("result: ", result)
    print("result_text: ", result_text)

    return result_text

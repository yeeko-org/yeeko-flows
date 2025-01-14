import re

from django.db.models import QuerySet
from infrastructure.assign.models import ParamValue


def update_parameters(
    query_param_value: QuerySet[ParamValue],
    parameters_dict: dict | None = None
) -> dict:
    if parameters_dict is None:
        parameters_dict = {}
    local_parameters = parameters_dict.copy()
    for param_value in query_param_value.values("parameter__name", "value"):
        param_name = param_value["parameter__name"]
        local_parameters[param_name] = param_value["value"]

    return local_parameters


def replace_parameter(extra_values_data: dict, text: str, default: str = ""):
    pattern = r"\{\{([\w.]+)\}\}"

    def get_nested_value(data, keys):
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]

            elif isinstance(data, list):
                if not data:
                    return default

                key = "0" if key == "first" else "-1" if key == "last" else key

                if key.isdigit() and int(key) < len(data):
                    data = data[int(key)]
                elif key == "count":
                    data = len(data)
                elif key == "sum":
                    data = sum(data)
                else:
                    return default

            elif isinstance(data, str) and key in ["lower", "upper"]:
                f_data = getattr(data, key)
                data = f_data()
            else:
                return default
        return data

    def replace_match(match):
        variable = match.group(1)
        keys = variable.split(".")
        if keys[0] not in extra_values_data:
            return default

        value = get_nested_value(extra_values_data[keys[0]], keys[1:])

        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, list):
            return str(value[0]) if value else default
        elif isinstance(value, dict):
            return default
        else:
            return str(value)

    result = re.sub(pattern, replace_match, text)
    result_text = re.sub(r'\s+', ' ', result.strip())
    print("--------------------")
    print("extra_values_data: ", extra_values_data)
    print("text: ", text)
    print("result: ", result)
    print("result_text: ", result_text)
    return result_text

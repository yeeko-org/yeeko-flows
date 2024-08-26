import json


def ensure_json_compatible(data: dict | list):

    def convert_value(value):
        if isinstance(value, dict):

            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):

            return [convert_value(v) for v in value]
        else:
            try:

                json.dumps(value)
                return value
            except (TypeError, OverflowError):

                return str(value)

    if isinstance(data, dict):
        return {k: convert_value(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_value(v) for v in data]
    else:
        return {}

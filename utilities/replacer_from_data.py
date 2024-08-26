import re


def replace_parameter(extra_values_data: dict, text: str, default: str = ""):
    pattern = r"\{\{(\w+)\}\}"

    def replace_match(match):
        key = match.group(1)
        if key in extra_values_data:
            return extra_values_data[key]
        else:
            return default

    result = re.sub(pattern, replace_match, text)

    result_text = re.sub(r'\s+', ' ', result.strip())

    print("--------------------")
    print("extra_values_data: ", extra_values_data)
    print("text: ", text)
    print("result: ", result)
    print("result_text: ", result_text)

    return result_text

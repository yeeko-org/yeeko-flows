def get_value_from_dict(data_dict, key):
    keys = key.split('.')
    value = data_dict
    try:
        for k in keys:
            if k.isdigit():
                k = int(k)
            value = value[k]
        return value
    except (KeyError, IndexError, TypeError):
        return None

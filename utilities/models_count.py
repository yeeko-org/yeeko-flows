from django.apps import apps


def models_count():

    all_models = apps.get_models()

    print()
    print("---Model counts:---")
    for model in all_models:
        model_name = model._meta.db_table
        count = model.objects.count()
        print(f"{model_name}: {count}")
    print("---End of model counts---")
    print()

def models_count_data():
    all_models = apps.get_models()
    data = {}
    for model in all_models:
        model_name = model._meta.db_table
        count = model.objects.count()
        data[model_name] = count
    return data

import importhook

@importhook.on_import('django.core')
def on_django_import(django):
    modified_django = importhook.copy_module(django)
    print("Modified django")
    return modified_django
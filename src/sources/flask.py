import importhook

@importhook.on_import('flask')
def on_django_import(flask):
    modified_flask = importhook.copy_module(flask)
    print("Modified flask")
    return modified_flask
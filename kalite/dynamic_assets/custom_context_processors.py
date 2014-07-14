from .finder import all_dynamic_settings


def dynamic_settings(request):
    '''
    Make all dynamic settings available to templates.
    '''

    return all_dynamic_settings()

import settings

if settings.CENTRAL_SERVER:
    import central.urls
    urlpatterns = central.urls.urlpatterns
else:    
    import main.urls
    urlpatterns = main.urls.urlpatterns


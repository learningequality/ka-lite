import settings

if settings.CENTRAL_SERVER:
    import central.urls
    urlpatterns = central.urls.urlpatterns
    handler404 = central.urls.handler404
    handler500 = central.urls.handler500
    
else:    
    import main.urls
    urlpatterns = main.urls.urlpatterns
    handler404 = main.urls.handler404
    handler500 = main.urls.handler500

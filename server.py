import os


def get_server_type(request):
    return request.META.get('SERVER_SOFTWARE')

def server_restart(request):
    server_type = get_server_type(request) or "UNKNOWN"

    if  server_type == "CherryPy/3.2.2 Server":
        import cherrypy
        cherrypy.engine.restart()
    elif "WSGIServer" in server_type: # dev server
        fpath = __file__.replace("pyc", "py")
        os.utime(fpath, None)   # we "touch" it to force the dev server to restart
    else:
        raise NotImplementedError("Do not know how to restart server of type %s" % server_type)

import os


def server_restart(server_type=""):
    if "cherrypy" in server_type.lower():
        import cherrypy
        cherrypy.engine.restart()
    elif "wsgiserver" in server_type.lower(): # dev server
        fpath = __file__.replace("pyc", "py")
        os.utime(fpath, None)   # we "touch" it to force the dev server to restart
    else:
        raise NotImplementedError("Do not know how to restart server of type %s" % server_type)

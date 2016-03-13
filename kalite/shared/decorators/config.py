def config_needed(handler):
    """
    Serve the configuration page only if it is determined
    that no configuration has previously been set
    """

    print "yes, config needed decorator function is being called"
    if is_configured():
        return HttpResponse("it's already configured")

    if request.path != '/facility/edit_config':
        #do not need this check because we're not intercepting every
        #single request/response
        #if response['Content-Type'].split(';')[0] == 'text/html':
        return does_database_exist(request)

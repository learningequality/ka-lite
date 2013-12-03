
class IfcfgError(Exception):
    """Generic Ifcfg Errors."""
    def __init__(self, msg):
        self.msg = msg
    
class IfcfgParserError(IfcfgError):
    """Ifcfg Parsing Errors."""
    def __init__(self, *args, **kw):
        super(IfcfgParserError, self).__init__(*args, **kw)
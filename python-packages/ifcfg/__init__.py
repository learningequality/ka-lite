
import platform
from . import meta
from . import parser
from . import tools
from . import exc

Log = tools.minimal_logger(__name__)

def get_parser(**kw):
    """
    Detect the proper parser class, and return it instantiated.
    
    Optional Arguments:
    
        parser
            The parser class to use instead of detecting the proper one.
            
        distro
            The distro to parse for (used for testing).
        
        kernel
            The kernel to parse for (used for testing).
        
        ifconfig
            The ifconfig (stdout) to pass to the parser (used for testing).
            
    """
    parser = kw.get('parser', None)
    ifconfig = kw.get('ifconfig', None)
    if not parser:
        distro = kw.get('distro', platform.system())
        full_kernel = kw.get('kernel', platform.uname()[2])
        kernel = '.'.join(full_kernel.split('.')[0:2]) 
        
        if distro == 'Linux':
            if float(kernel) < 3.3:
                from .parser import Linux2Parser as LinuxParser
            else:
                from .parser import LinuxParser
            parser = LinuxParser(ifconfig=ifconfig)
        elif distro in ['Darwin', 'MacOSX']:
            from .parser import MacOSXParser
            parser = MacOSXParser(ifconfig=ifconfig)
        else:
            raise exc.IfcfgParserError("Unknown distro type '%s'." % distro)
    
    Log.debug("Distro detected as '%s'" % distro)
    Log.debug("Using '%s'" % parser)        
    return parser
    
def interfaces():
    """
    Return just the parsed interfaces dictionary from the proper parser.
    
    """
    parser = get_parser()
    return parser.interfaces

def default_interface():
    """
    Return just the default interface device dictionary.
    
    """
    parser = get_parser()
    return parser.default_interface


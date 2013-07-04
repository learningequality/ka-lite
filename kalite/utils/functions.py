def isnumeric(obj):
    """Returns whether an object is itself numeric, or can be converted to numeric"""
    
    try:
        float(obj)
        return True
    except:
        return False
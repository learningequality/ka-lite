
def convert_value(value, datatype):      
    if datatype == "int":
        return int(value)
    if datatype == "float":
        return float(value)
    if datatype == "bool":
        return bool(value=='True' or value=='1')
    return value

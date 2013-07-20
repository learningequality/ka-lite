class AttrDict(dict):

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        
    def __getattr__(self, name):
        value = self[name]
        if type(value) == dict:
            value = AttrDict(value)
        if type(value) == list:
            for i in range(len(value)):
                if type(value[i]) == dict:
                    value[i] = AttrDict(value[i])
        return value

    def __setattr__(self, name, value):
        self[name] = value

class APIModel(AttrDict):
    
    _related_field_types = {} # this is a dummy; do not use directly
    
    def __init__(self, *args, **kwargs):
        
        super(APIModel, self).__init__(*args, **kwargs)
                
        for name in getattr(self, "_related_field_types", {}):
            if name in self:
                # convert dicts to the related type
                if type(self[name]) == dict:
                    self[name] = self._related_field_types[name](self[name])
                # convert every item in related list to correct type
                elif type(self[name]) == list:
                    for i in range(len(self[name])):
                        self[name][i] = self._related_field_types[name](self[name][i])

def class_by_kind(node):
    return kind_to_class_map[node["kind"]](node)



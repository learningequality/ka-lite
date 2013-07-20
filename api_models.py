
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
                    convert_list_to_classes(self[name], class_converter=self._related_field_types[name])
                    

def class_by_kind(node):
    return kind_to_class_map[node["kind"]](node)


def convert_list_to_classes(nodelist, class_converter=class_by_kind):
    """
    Convert each element of the list (in-place) into an instance of a subclass of APIModel.
    You can pass a particular class to `class_converter` if you want to, or it will auto-select by kind.
    """
    
    for i in range(len(nodelist)):
        nodelist[i] = class_converter(nodelist[i])
    
    return nodelist # just for good measure; it's already been changed
    

class Video(APIModel):
    pass

class Exercise(APIModel):
    pass

class Topic(APIModel):
    
    _related_field_types = {
        "children": class_by_kind,
    }

class User(APIModel):
    pass

class Badge(APIModel):
    pass

class UserExercise(APIModel):
    pass

class UserVideo(APIModel):
    pass

#ProblemLog and VideoLog API calls return multiple entities in a list

class ProblemLog(APIModel):
    pass

class VideoLog(APIModel):
    pass


kind_to_class_map = {
    "video": Video,
    "exercise": Exercise,
    "topic": Topic,
}    

t = Topic({
    "name": "Penguin Watchers", 
    "children":
        [
            {
                "kind": "video",
                "name": "Waddling"
            }, 
            {
                "kind": "exercise",
                "name": "Waddle Test"
            },
            {
                "kind": "topic",
                "name": "More stuff",
                "children": [
                    {
                        "kind": "video",
                        "name": "Deep Secrets"
                    }
                ]
            },
        ],
})

if __name__ == "__main__":
    print t.name
    print t.children
    print t.children[0].__class__
    print t.children[1].__class__


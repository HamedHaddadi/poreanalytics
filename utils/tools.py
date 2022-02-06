
import numpy as np 
from os import listdir
from natsort import natsorted

# ##### useful functions ##### #
list_files = lambda file_path, file_name: natsorted([_file for _file in listdir(file_path) if file_name in _file], key= lambda y: y.lower())

def generate_RGB(number):
    return [((1/255)*np.random.randint(0, 255), (1/255)*np.random.randint(0, 255), 
                (1/255)*np.random.randint(0, 255)) for num in range(number)]

# #### usefule containers #### #
class GroupDict(dict):

    def __init__(self, *args):
        super().__init__(self)
        if args:
            self[args[0]] = set(args[1:])
    
    def __setitem__(self, new_key, new_value):
        if len(self.items()) == 0:
            super().__setitem__(new_key, new_value)
        else:
            found = False
            for key, value in self.items():
                if not value.isdisjoint(new_value):
                    value |= set(new_value)
                    super().__setitem__(key, value)
                    found = True
            if not found:
                super().__setitem__(new_key, set(new_value))
    
    def __getitem__(self, key):
        return super().__getitem__(key)
    
    def __iter__(self):
        return (list(self[key]) for key in self.keys())
            
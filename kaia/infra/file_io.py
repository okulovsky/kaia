from typing import *
import pickle
import json
from pathlib import Path
import os

class FileIO:
    @staticmethod
    def read_bytes(filename):
        with open(filename, 'rb') as file:
            return file.read()

    @staticmethod
    def read_pickle(filename):
        with open(filename,'rb') as file:
            return pickle.load(file)

    @staticmethod
    def read_json(filename, as_obj = False):
        with open(filename,'r') as file:
            result = json.load(file)
            return result

    @staticmethod
    def read_text(filename, encoding='utf-8'):
        with open(filename,'r', encoding=encoding) as file:
            return file.read()


    @staticmethod
    def write_pickle(data, filename):
        with open(filename,'wb') as file:
            pickle.dump(data,file)

    @staticmethod
    def write_json(data, filename):
        with open(filename,'w') as file:
            json.dump(data,file,indent=1)

    @staticmethod
    def write_text(data, filename):
        with open(filename,'w') as file:
            file.write(data)


    @staticmethod
    def folder(location: Union[Path, str], pattern: str = '*'):
        if isinstance(location, str):
            location = Path(location)
        elif isinstance(location, Path):
            pass
        else:
            raise ValueError('Location should be either str or Path, but was {0}, {1}'.format(type(location), location))

        if not os.path.isdir(location):
            raise ValueError('{0} is not a directory'.format(location))

        return location.glob(pattern)
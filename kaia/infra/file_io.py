import pickle
import json
import jsonpickle

class FileIO:
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
    def read_text(filename):
        with open(filename,'r') as file:
            return file.read()

    @staticmethod
    def read_jsonpickle(filename):
        with open(filename,'r') as file:
            return jsonpickle.loads(file.read())

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
    def write_jsonpickle(data, filename):
        with open(filename,'w') as file:
            file.write(jsonpickle.dumps(data))

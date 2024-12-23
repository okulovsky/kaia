import traceback
import flask
import os

class BoilerplateApp:
    def __init__(self, setting: str, model: str):
        self.setting = setting
        self.model = model


    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/decide', view_func=self.decide, methods = ['POST'])
        app.add_url_rule('/model', view_func=self.get_model, methods=['GET'])
        app.add_url_rule('/resources', view_func=self.resources, methods=['GET'])
        return app

    def index(self):
        return "OK"

    def get_model(self):
        return self.model

    def decide(self):
        try:
            data = flask.request.json
            return flask.jsonify(dict(
                argument=data['argument'],
                setting = self.setting,
                model=self.model
            ))
        except:
            return traceback.format_exc(), 500

    def resources(self):
        folder_contents = {}
        path = '/resources'
        for root, _, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, path)
                with open(file_path, 'r', encoding='utf-8') as file:
                    folder_contents[relative_path] = file.read()
        return folder_contents
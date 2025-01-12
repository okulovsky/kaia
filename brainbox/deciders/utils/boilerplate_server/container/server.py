import traceback
import flask
import os

class BoilerplateServerApp:
    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/echo', view_func=self.decide, methods = ['POST'])
        return app

    def index(self):
        return "OK"


    def decide(self):
        try:
            data = flask.request.json
            return flask.jsonify(dict(
                arguments=data,
                success = True
            ))
        except:
            return traceback.format_exc(), 500

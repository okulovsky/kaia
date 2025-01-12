import traceback
import flask
from runner import run_espeak

class EspeakPhonemizerApp:
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
            result = run_espeak(data)
            return flask.jsonify(result)
        except:
            return traceback.format_exc(), 500

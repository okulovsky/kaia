from flask import Flask
from phonix.server.monitoring import create_dash_app, PhonixMonitoring
from phonix.server.monitoring.sample_generator import SampleGenerator

app = Flask(__name__)

dash_app = create_dash_app(PhonixMonitoring(SampleGenerator()))
dash_app.init_app(app)  # Correct binding

@app.route('/')
def index():
    return '<h1>Main Page</h1><p>Go to <a href="/monitor">/monitor</a></p>'

if __name__ == '__main__':
    app.run(debug=True)

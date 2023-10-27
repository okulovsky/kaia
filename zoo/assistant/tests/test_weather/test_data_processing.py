from yo_fluq_ds import FileIO
from pathlib import Path
from unittest import TestCase
from zoo.assistant.skills.weather.data_processing import make_all

reply = FileIO.read_json(Path(__file__).parent/'reply.json')
class WeatherProcessingTestCase(TestCase):
    def test_all(self):
        forecast = make_all(reply)
        result = ' '.join(f.template.to_str(f.value) for f in forecast)
        print(result)
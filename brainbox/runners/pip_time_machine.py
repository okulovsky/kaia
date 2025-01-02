import traceback
from typing import *
from datetime import datetime
from brainbox.framework import Loc
from yo_fluq import FileIO
from dateutil import parser
import pandas as pd
import requests
import time
import os

class PipTimeMachine:
    def __init__(self,
                 cutoff_timestamp: datetime,
                 sleep: float = 0.1,
                 cache_folder = Loc.temp_folder /'time_machine_cache'
                 ):
        self.cutoff_timestamp = cutoff_timestamp
        self.sleep = sleep
        os.makedirs(cache_folder, exist_ok=True)
        self.cache_folder = cache_folder

    def _info_to_timetable(self, info):
        rows = []

        for version, release in info['releases'].items():
            for item in release:
                rows.append(dict(version=version, timestamp = parser.parse(item['upload_time_iso_8601'])))
        df = pd.DataFrame(rows)
        df['timestamp'] = df.timestamp.dt.tz_localize(None)
        return df

    def _process_package(self, package_name: str):
        cache_path = self.cache_folder /package_name
        if cache_path.is_file():
            info = FileIO.read_json(cache_path)
        else:
            reply = requests.get(f'https://pypi.org/pypi/{package_name}/json')
            try:
                info = reply.json()
                FileIO.write_json(info, cache_path)
            except:
                print(package_name)
                print(reply.text)
                raise
            time.sleep(self.sleep)

        df = self._info_to_timetable(info)
        s = df.loc[df.timestamp<=self.cutoff_timestamp].sort_values('timestamp' ,ascending=False)
        if s.shape[0] == 0:
            return None
        return s.version.iloc[0]

    def process_packages(self, package_names: Iterable[str]):
        rows = []
        for name in package_names:
            rows.append(dict(package=name ,version=self._process_package(name)))
        return rows

    def process_pip_freeze(self, pip_freeze: Iterable[str]):
        package_names = [z.split('==')[0] for z in pip_freeze if z.strip()!='']
        with_versions = self.process_packages(package_names)
        return '\n'.join([p['package']+'=='+p['version'] for p in with_versions])

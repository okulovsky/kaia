import os

from kaia.bro.amenities.conbee import Driver, Parser
from pprint import pprint

import requests

if __name__ == '__main__':
    #print('{0}/api/{1}/sensors'.format(os.environ['CONBEE_URL'], os.environ['CONBEE_PASSWORD']))
    url = os.environ['CONBEE_URL']
    pwd = os.environ['CONBEE_PASSWORD']
    driver = Driver(url, pwd)
    data = driver.get_current().get_data()
    pprint([(key,value) for key,value in data['sensors'].items() if value['uniqueid'] == '00:15:8d:00:07:74:33:db-01-0201'])
    pprint(data)
    #reply = requests.put(f'{url}/api/{pwd}/sensors/6/config', json=dict(heatsetpoint=2050))
    #reply = requests.put(f'{url}/api/{pwd}/sensors/6/state', json=dict(valve=0))
    #print(reply.json())


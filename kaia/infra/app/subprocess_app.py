from kaia.infra.comm import Sql
from kaia.infra.app.subprocess_runner import get_filename
from threading import Thread
import time
import sys
import traceback
import os

entry = None

def monitor_termination(id):
    messenger = Sql.file(get_filename()).messenger()
    while True:
        msg = messenger.Query(tags=['down',id]).query_single_or_default(messenger)
        if msg is None:
            time.sleep(0.1)
            continue
        messenger.close(msg.id, None)
        if hasattr(entry, 'terminate'):
            entry.terminate()
        os._exit(0)
        break



if __name__ == '__main__':
    uid = sys.argv[1]
    Thread(target=monitor_termination, args=[uid]).start()
    messenger = Sql.file(get_filename()).messenger()
    msg = messenger.Query(uid).query_single_or_default(messenger)
    if msg is None:
        raise ValueError('No initialization message is available')
    try:
        entry = msg.payload
    except:
        rep = traceback.format_exc()
        messenger.close(msg.id, rep)
    messenger.close(msg.id, None)
    entry()
from simple_avatar_client import SimpleAvatarClient, Message
from rpi_commands import *
import argparse
import time
import traceback

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Raspberry Pi Kaia Daemon')
    parser.add_argument("-u", "--base-url")
    parser.add_argument("-s", "--session")
    args = parser.parse_args()
    base_url = 'http://192.168.178.48:13002'
    session = 'default'
    print(f"Running with {base_url}, session {session}")
    while True:
        try:
            client = SimpleAvatarClient(base_url, session, ['VolumeCommand'])
            client.scroll_to_end()
            print("Client connected")
            while True:
                messages = client.pull()
                for message in messages:
                    print(message)
                    if message.message_type.endswith("VolumeCommand"):
                        set_volume(message.payload['value'])

        except Exception:
            print("Exception:")
            print(traceback.format_exc())
            print('\n\nRestarting in 1 second')
            time.sleep(1)



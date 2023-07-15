from queue import Queue
import pexpect
import re
import time
import sys
import threading


class SmartLabReaderConverter:
    def __init__(self, queue: Queue = None):
        self.queue = queue

    def _run(self):
        MAC = '04:a3:16:a1:81:cc'
        while True:
            gatt = pexpect.spawn("gatttool -b " + MAC + " -I")
            try:
                gatt.sendline('connect')
                gatt.expect("Connection successful")

                gatt.sendline("char-write-cmd 0x0017 0100")
                while (True):
                    readings = gatt.read_nonblocking(100000).decode('utf-8')
                    matches = re.findall('Notification handle = 0x0016 value: (.{23})', readings)
                    for match in matches:
                        weight = int(match[6:8] + match[3:5], 16)
                        if self.queue is None:
                            print(f'{weight}           \r')
                        else:
                            self.queue.put(weight)
                    if 'Invalid file descriptor' in readings:
                        raise ValueError('Scales off')
                    time.sleep(0.1)
            except KeyboardInterrupt:
                break
            except:
                type, value, trace = sys.exc_info()
                print(type, value)
                gatt.close()

    @staticmethod
    def run(queue):
        reader = SmartLabReaderConverter(queue)
        thread = threading.Thread(target = reader._run)
        thread.start()



if __name__ == '__main__':
    SmartLabReaderConverter()._run()

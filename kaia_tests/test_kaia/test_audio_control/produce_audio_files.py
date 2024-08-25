from kaia.brainbox.deciders.docker_based import (OpenTTSInstaller, OpenTTSSettings)
import wave
import struct

settings = OpenTTSSettings()
installer = OpenTTSInstaller(settings)

def produce(text):
    data = installer.create_api().call(text)
    fname = text.lower().replace(' ','_')+'.wav'
    with open('files/'+fname, 'wb') as file:
        file.write(data)

def produce_silence():
    wavfile = wave.open('files/silence.wav', 'w')
    rate = 22050
    wavfile.setparams((1, 2, rate, 512, "NONE", "NONE"))
    for i in range(11*rate//512):
        data = [0 for _ in range(512)]
        wavfile.writeframes(struct.pack("h" * len(data), *data))
    wavfile.close()

if __name__ == '__main__':
    installer.run_in_any_case_and_create_api()
    #produce('Computer')
    #produce('Are you here')
    #produce('Repeat after me')
    #produce("Make me a sandwich")
    produce_silence()

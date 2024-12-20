from kaia.brainbox.deciders.recognizer.installer import RecognizerInstaller
from kaia.brainbox.deciders.recognizer.settings import RecognizerSettings

if __name__ == '__main__':
    installer = RecognizerInstaller(RecognizerSettings)
    installer.run_in_any_case_and_create_api()
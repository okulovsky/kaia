from kaia.brainbox.deciders.faces_recognizer.installer import FacesRecognizerInstaller
from kaia.brainbox.deciders.faces_recognizer.settings import FacesRecognizerSettings

if __name__ == '__main__':
    installer = FacesRecognizerInstaller(FacesRecognizerSettings)
    installer.run_in_any_case_and_create_api()
    # installer.brainbox_self_test()
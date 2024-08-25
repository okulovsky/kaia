from kaia.brainbox.deciders.whisper.installer import WhisperInstaller, WhisperSettings

if __name__ == '__main__':
    installer = WhisperInstaller(WhisperSettings())
    installer.run_in_any_case_and_create_api()



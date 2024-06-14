from kaia.ml.voice_cloning.coqui_training_container.installer import CoquiTrainingContainerSettings, CoquiTrainingContainerInstaller

if __name__ == '__main__':
    installer = CoquiTrainingContainerInstaller(CoquiTrainingContainerSettings())
    installer.reinstall()
    installer.notebook_endpoint.run()

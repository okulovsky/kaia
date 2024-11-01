from kaia.brainbox.deciders.wd14_tagger import WD14TaggerSettings, WD14TaggerInstaller

if __name__ == '__main__':
    installer = WD14TaggerInstaller(WD14TaggerSettings())
    installer.reinstall()
    #installer.notebook_service.run()
    installer.run_if_not_running_and_wait()
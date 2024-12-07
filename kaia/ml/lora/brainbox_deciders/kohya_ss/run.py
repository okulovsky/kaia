from kaia.ml.lora.brainbox_deciders.kohya_ss import KohyaSSSettings, KohyaSSInstaller, KohyaSS
from kaia.brainbox.core.small_classes import ArgumentsValidator

def test(a,b,*,c):
    pass

if __name__ == '__main__':
    installer = KohyaSSInstaller(KohyaSSSettings())
    #installer.install()
    installer.gradio_service.run()
    #installer.brainbox_self_test()




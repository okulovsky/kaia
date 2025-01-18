from brainbox.deciders import BoilerplateOnDemand

if __name__ == '__main__':
    controller = BoilerplateOnDemand.Controller()
    controller.install()
    controller.self_test()
from demos.kaia.main import create_app

if __name__ == '__main__':
    app = create_app()
    app.app.run()
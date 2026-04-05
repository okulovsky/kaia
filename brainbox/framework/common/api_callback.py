class ApiCallback:
    def report_progress(self, progress: float):
        pass

    def log(self, s):
        print(s)

    def report_responding(self, filename: str):
        pass



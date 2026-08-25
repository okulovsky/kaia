from foundation_kaia.marshalling import endpoint, service

@service
class ICreativeArticulator:
    @endpoint
    def synchronize(self):
        pass

    @endpoint(force_json_params=True)
    def update(self, id: str, text: str):
        pass

    @endpoint(force_json_params=True)
    def generate(self, id: str, before_selection: str, selection: str, after_selection: str, action: str) -> str:
        pass
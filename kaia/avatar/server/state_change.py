class StateChange:
    def __init__(self, api, changes):
        self.api = api
        self.changes = changes
        self.current_state: dict|None = None

    def __enter__(self):
        self.current_state = self.api.state_get()
        self.api.state_change(self.changes)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        reverse = {
            key:value
            for key,value in self.current_state.items()
            if key in self.changes
        }
        for key in self.changes:
            if key not in self.current_state:
                reverse[key] = None
        self.api.state_change(reverse)



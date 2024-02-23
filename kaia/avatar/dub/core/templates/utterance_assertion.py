

class UtteranceAssertion:
    def __init__(self, expected):
        self.expected = expected

    def template_only(self, actual):
        if self.expected.template.name != actual.template.name:
            raise ValueError(f'Wrong template: expected {self.expected.template.name}, actual {actual.template.name}')
        return True

    def __call__(self, actual):
        if type(actual).__name__ !='Utterance':
            raise ValueError(f"Expected utterance, got {actual}")

        self.template_only(actual)

        if isinstance(self.expected.value, dict):
            if not isinstance(actual.value, dict):
                raise ValueError(f'Expected dict value, actial is {type(actual.value)}')
            else:
                expected_keys = tuple(sorted(self.expected.value))
                actual_keys = tuple(sorted(actual.value))
                if expected_keys!=actual_keys:
                    raise ValueError(f'Expected keys {expected_keys}, actual {actual_keys}')
                for key in expected_keys:
                    if self.expected.value[key] != actual.value[key]:
                        raise ValueError(f"Value at key {key}, expected {self.expected.value[key]}, actual {actual.value[key]}")
        else:
            if isinstance(actual.value, dict):
                raise ValueError(f'Expected value of type {type(self.expected.value)} actual value was dict')
            if self.expected.value!=actual.value:
                raise ValueError(f'Expected value {self.expected.value}, actual {actual.value}')
        return True


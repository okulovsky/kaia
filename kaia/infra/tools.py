class Tools:
    @staticmethod
    def check_dict_equals_keys_and_values(d1, d2):
        if not isinstance(d1, dict) or not isinstance(d2, dict):
            return False, False
        true_keys = tuple(sorted(d1))
        actual_keys = tuple(sorted(d2))
        if true_keys != actual_keys:
            return False, False

        for key in true_keys:
            if d1[key] != d2[key]:
                return True, False

        return True, True

    @staticmethod
    def check_dict_equals(d1, d2):
        k, v = Tools.check_dict_equals_keys_and_values(d1, d2)
        return k and v
from .test_time_factory import TestTimeFactory

def slice(condition, hit_count: int = 1):
    def _(q):
        hits = 0
        result = []
        for e in q:
            result.append(e)
            if condition(e):
                hits+=1
                if hits>=hit_count:
                    return result
    return _
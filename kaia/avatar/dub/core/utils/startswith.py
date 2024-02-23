#TODO: This implementation is very sub-optimal. We need prefix trees
class Startswith:
    def __init__(self, s, index):
        self.s = s
        self.index = index
        while self.index < len(self.s) and self.s[self.index].isspace():
            self.index += 1

    def startswith(self,  w):
        w = w.strip()
        if len(w) == 0:
            return self.index
        stwith = self.s.startswith(w, self.index)
        if not stwith:
            return None
        index = self.index
        index += len(w)
        if index == len(self.s):
            return index
        if self.s[index].isalpha():
            return None
        return index
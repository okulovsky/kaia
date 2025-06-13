from unittest import TestCase
from avatar.media_library_manager.strategies import get_random_weighed_element
import pandas as pd

class RandomWeightedElementTestCase(TestCase):
    def test(self):
        elements = [1,2,3,4]
        rnd = []
        for i in range(10000):
            rnd.append(get_random_weighed_element(elements))
        s = pd.Series(rnd).to_frame('x').groupby('x').size().to_dict()
        for i in range(4):
            delta = s[i]/(1000*(i+1))
            self.assertLess(abs(1-delta),0.2)

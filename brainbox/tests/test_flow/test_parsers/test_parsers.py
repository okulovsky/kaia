from brainbox.flow import BulletPointParser
from unittest import TestCase

bullet_point = '''
Here are some bullet point for you
* First
* Second

and then after awhile

* Third

And here some long explanation, why the bullet points are like this.

'''

class ParsersTestCase(TestCase):
    def test_bullet_point_list(self):
        result = BulletPointParser()(bullet_point)
        self.assertEqual(['First', 'Second', 'Third'], result)

    def test_bullet_point_joint(self):
        result = BulletPointParser().joint()(bullet_point)
        self.assertEqual('First, Second, Third', result)

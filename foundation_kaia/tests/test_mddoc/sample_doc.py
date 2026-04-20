from foundation_kaia.releasing.mddoc import ControlValue

cv = ControlValue.mddoc_define_control_value(3)

'''
# Sample Documentation

This module demonstrates all mddoc features.

Here is some code:

```
code inside text
```

And some closing text.

Now, let's compute:
'''

x = 1 + 2

"""
The result should be:
"""

cv.mddoc_validate_control_value(x)

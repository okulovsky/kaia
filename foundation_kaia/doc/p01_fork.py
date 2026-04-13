"""
## Fork

Fork is a small utility to run the functions in a different subprocess: particularly the web-servers to ensure full isolation.

You can define the callable, and then use Fork like this:

```
from foundation_kaia import Fork

with Fork(callable):
    # Do useful work
    pass
```

There are also `.start()` and `.terminate()` methods if you do not want to use the context manager.
Mostly, `Fork` is used for unit testing and the documentation purposes, so, with the context manager.
"""
import time
import inspect
from functools import wraps


def timer(include_doc=False):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            start = time.time()
            ret = func(*args, **kwargs)
            module = inspect.getmodule(func)
            class_name = None
            if module and module.__name__ != "__main__":
                module = module.__name__
            if args and hasattr(args[0], '__dict__'):
                class_name = args[0].__class__.__name__

            print(f'< {str(module):<35}'
                  f'< class : {str(class_name):<20}'
                  f'< function : {str(func.__name__):<20}'
                  f'< duration : {round(time.time() - start, 4)} sec >')

            if include_doc and func.__doc__:
                print("< doc >")
                print(func.__doc__)

            return ret
        return inner
    return wrapper

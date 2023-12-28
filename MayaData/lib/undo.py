from maya import cmds


class Singleton(type):
    """
    Singleton wrapper for metaclass instancing.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class UndoContext(object):
    """
    Undo Context wrapper for maya. Will undo any codeblock within it's with: block.
    """

    __metaclass__ = Singleton

    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, num):
        self._count = num

    def __enter__(self):
        if self.count == 0:
            cmds.undoInfo(openChunk=True)
        self.count += 1

    def __exit__(self, *exc_info):
        self.count -= 1
        if self.count == 0:
            cmds.undoInfo(closeChunk=True)

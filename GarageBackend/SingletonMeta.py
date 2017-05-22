
from threading import Lock

class SingletonMeta(type):
    __instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in SingletonMeta.__instances:
            SingletonMeta.__instances[cls] = super().__call__(*args, **kwargs)
        return SingletonMeta.__instances[cls]

# class Test(metaclass=SingletonMeta):
#     pass
#
# t1 = Test()
# t2 = Test()
#
# print(t1, t2)
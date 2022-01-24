import functools


class wrapper_base:
    def __init__(self, func, sync_obj, logger):
        functools.update_wrapper(self, func)
        self.func = func
        self.sync_obj = sync_obj
        self.logger = logger

    # for decorating class methods(bound methods)
    def __get__(self, instance, owner):
        return functools.partial(self.__call__, instance)

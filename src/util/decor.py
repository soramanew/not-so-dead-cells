from functools import wraps
from types import MethodType


def _reset_run_once(self):
    self.has_run = False


def _fake_run_once(self):
    self.has_run = True


def run_once(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    wrapper.reset = MethodType(_reset_run_once, wrapper)
    wrapper.fake_run = MethodType(_fake_run_once, wrapper)
    return wrapper

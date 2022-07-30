__all__ = ["LoginError", "RequestError", "NoExistError"]


class LoginError(Exception):
    pass


class NoExistError(Exception):
    pass


class RequestError(Exception):
    pass

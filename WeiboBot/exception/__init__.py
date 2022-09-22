__all__ = ["LoginError", "RequestError", "NoExistError", "UploadError"]


class LoginError(Exception):
    pass


class NoExistError(Exception):
    pass


class RequestError(Exception):
    pass


class UploadError(Exception):
    pass

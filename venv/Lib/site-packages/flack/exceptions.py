# coding=utf-8
__all__ = ["SlackTokenError", "OAuthConfigError", "OAuthResponseError"]


class SlackTokenError(Exception):
    pass


class OAuthConfigError(Exception):
    pass


class OAuthResponseError(Exception):
    pass

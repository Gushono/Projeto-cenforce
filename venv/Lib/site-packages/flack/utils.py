# coding=utf-8
__all__ = ["slack_username", ]


def slack_username(id):
    return "<@{}>".format(id)

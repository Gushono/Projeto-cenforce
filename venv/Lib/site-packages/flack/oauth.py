# coding=utf-8
import logging
from functools import wraps
from collections import namedtuple

from requests import post, HTTPError
from flask import request, render_template
from flask import current_app as app

from .exceptions import OAuthConfigError, OAuthResponseError

__all__ = ["render_button", "callback", ]

logger = logging.getLogger(__name__)

DEFAULT_OAUTH_SCOPE = "commands,users:read,channels:read,chat:write:bot"
OAUTH_CREDENTIALS = namedtuple(
    "oauth_credentials",
    ("team_id", "access_token", "scope")
)


def render_button():
    if not app.config.get("FLACK_CLIENT_ID"):
        raise OAuthConfigError("Requires client id")

    logger.debug("Rendering oauth button")
    return render_template("oauth_button.tpl",
                           client_id=app.config["FLACK_CLIENT_ID"],
                           auth_scope=(app.config["FLACK_SCOPE"]
                                       or DEFAULT_OAUTH_SCOPE))


def _oauth_callback_response(code):
    try:
        response = {
            "code": code,
            "client_id": app.config["FLACK_CLIENT_ID"],
            "client_secret": app.config["FLACK_CLIENT_SECRET"]
        }

        logger.debug(u"Requesting OAuth Credentials: {!r}".format(response))
        response = post("https://slack.com/api/oauth.access", data=response)
        response.raise_for_status()

        logger.debug(u"Slack response: {!r}".format(response.text))

        oauth_response = response.json()
        logger.info(u"Received new OAuth credentials for team: {!r}".format(
            oauth_response["team_id"]))

    except HTTPError:
        raise OAuthResponseError("Slack rejected the request")

    except Exception:
        raise OAuthResponseError("Unknown error")

    else:
        return OAUTH_CREDENTIALS(team_id=oauth_response["team_id"],
                                 access_token=oauth_response["access_token"],
                                 scope=oauth_response["scope"])


def callback(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if (not app.config.get("FLACK_CLIENT_ID")
                and app.config.get("FLACK_CLIENT_SECRET")):
            raise OAuthConfigError("Requires client id and secret")

        code = request.args["code"]
        logger.info(u"OAuth callback called with code: {!r}".format(code))

        credentials = _oauth_callback_response(code)
        kwargs.updatee(credentials=credentials)

        return fn(*args, **kwargs)

    return wrapper

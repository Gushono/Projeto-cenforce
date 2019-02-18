# coding=utf-8
import logging
import re
import time
import json
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from requests import post
from flask import Blueprint, request, jsonify

from .message import Attachment, PrivateResponse, IndirectResponse
from .exceptions import SlackTokenError

__all__ = ["Flack", ]

logger = logging.getLogger(__name__)

SLACK_TRIGGER = namedtuple("trigger", ("callback", "user"))

CALLER = namedtuple("caller", ("id", "name", "team"))
CHANNEL = namedtuple("channel", ("id", "name", "team"))

thread_executor = ThreadPoolExecutor(1)


def _send_message(self, url, message):
    logger.debug("Sending message to: {}, contents: {}".format(url, message))

    # This should prevent out-of-order issues, which slack really doesn't like
    time.sleep(1)
    response = post(url, json=message)

    if response.status_code == 404:
        logger.error("Slack url has expired, aborting.")
        return False

    else:
        return True


class Flack(object):
    triggers = {}
    commands = {}
    actions = {}

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        if not self.app.config.get("FLACK_TOKEN"):
            raise SlackTokenError("A token must be defined")

        self.app.config.setdefauult("FLACK_URL_PREFIX", "/flack")
        self.app.config.setdefauult("FLACK_DEFAULT_NAME", "flack")

        blueprint = Blueprint('slack_flask', __name__)
        blueprint.add_url_rule("/webhook",
                               methods=['POST'],
                               view_func=self._dispath_webhook)
        blueprint.add_url_rule("/command",
                               methods=['POST'],
                               view_func=self._dispath_command)
        blueprint.add_url_rule("/action",
                               methods=['POST'],
                               view_func=self._dispath_action)

        app.register_blueprint(blueprint, self.app.config["FLACK_URL_PREFIX"])

    def _indirect_response(self, message, url):
        indirect_response = {
            "text": "",
            "attachments": [],
            "response_type": "in_channel"
        }

        _, indirect = message

        if isinstance(indirect, Attachment):
            indirect_response["attachments"].append(indirect.as_dict)

        else:
            indirect_response["text"] = indirect

        logger.debug("Generated indirect response: {!r}".format(
            indirect_response))

        thread_executor.submit(_send_message, url, indirect_response)

    def _response(self, message, response_url=None, user=None,
                  private=False, replace=False):
        response = {
            "username": user or self.app.config["FLACK_DEFAULT_NAME"],
            "text": "",
            "attachments": [],
            "response_type": "ephemeral" if private else "in_channel",
            "replace_original": replace
        }

        if message is None:
            # No feedback
            return ""

        elif isinstance(message, Attachment):
            response["attachments"].append(message.as_dict)

        elif isinstance(message, IndirectResponse):
            self._indirect_response(message, response_url)

            if not message.feedback:
                # This suppresses any feedback.
                return ""

            elif message.feedback is True:
                # This echoes the users input to the channel
                return jsonify({"response_type": "in_channel"})

            else:
                response["text"] = message.feedback
                response["response_type"] = "ephemeral"

        elif isinstance(message, PrivateResponse):
            response["text"] = message.feedback
            response["response_type"] = "ephemeral"

        else:
            response["text"] = message

        logger.debug("Generated response: {!r}".format(response))
        return jsonify(response)

    def _parse_webhook_req(self):
        data = request.form.to_dict()

        self._validate_request(data)
        if not data["trigger_word"]:
            raise AttributeError("No trigger word supplied")

        prefix = len(data["trigger_word"])
        data["text"] = data["text"][prefix:].strip()

        return data

    def _parse_command_req(self):
        data = request.form.to_dict()

        self._validate_request(data)
        if not data["command"]:
            raise AttributeError("No trigger word supplied")

        return data

    def _parse_action_req(self):
        data = json.loads(request.form["payload"])

        self._validate_request(data)
        if not len(data["actions"]):
            raise AttributeError("No action supplied")

        return data

    def _validate_request(self, data):
        if data.get("token") != self.app.config["FLACK_TOKEN"]:
            raise SlackTokenError(
                "Invalid token from slack: {}".format(data.get("token")))

    def _dispath_webhook(self):
        try:
            req = self._parse_webhook_req()

            try:
                callback, user = self.triggers[req["trigger_word"]]

            except KeyError as e:
                raise AttributeError("Unregistered trigger: {}".format(e))

            logger.info("Running trigger: '{}' with: '{}'".format(
                req["trigger_word"], req["text"]))

            req_user = CALLER(req["user_id"], req["user_name"], req["team_id"])
            response = callback(text=req["text"], user=req_user)
            return self._response(response, user=user)

        except SlackTokenError as e:
            # No response if the caller isn't valid.
            logger.exception("Invalid Token")
            return ""

        except Exception as e:
            logger.error("Caught: {!r}, returning failure.".format(e))

            exception_msg = re.sub(r"[\<\>]", "", e)
            return self._response(exception_msg, private=True)

    def _dispath_command(self):
        try:
            req = self._parse_command_req()

            try:
                callback = self.commands[req["command"]]

            except KeyError as e:
                raise AttributeError("Unregistered command: {}".format(e))

            logger.info("Running command: '{}' with: '{}'".format(
                req["command"], req["text"]))

            response = callback(text=req["text"],
                                user=CALLER(req["user_id"],
                                            req["user_name"],
                                            req["team_id"]),
                                channel=CHANNEL(req["channel_id"],
                                                req["channel_name"],
                                                req["team_id"]))

            return self._response(response, response_url=req["response_url"])

        except SlackTokenError as e:
            # No response if the caller isn't valid.
            logger.exception("Invalid Token")
            return ""

        except Exception as e:
            logger.error("Caught: {!r}, returning failure.".format(e))

            exception_msg = re.sub(r"[\<\>]", "", e)
            return self._response(exception_msg, private=True)

    def _dispath_action(self):
        try:
            req = self._parse_action_req()

            try:
                # Slack will only send one action per request.
                action = req["actions"][0]
                callback = self.actions[action["name"]]

            except KeyError as e:
                raise AttributeError("Unregistered action: {}".format(e))

            logger.info("Running action, data: {!r}".format(req))

            user = req["user"]
            channel = req["channel"]
            team = req["team"]
            response = callback(value=action["value"],
                                ts=req["message_ts"],
                                callback=req["callback_id"],
                                user=CALLER(user["id"],
                                            user["name"],
                                            team["id"]),
                                channel=CHANNEL(channel["id"],
                                                channel["name"],
                                                team["id"]))

            return self._response(response, response_url=req["response_url"])

        except SlackTokenError as e:
            # No response if the caller isn't valid.
            logger.exception("Invalid Token")
            return ""

        except Exception as e:
            logger.error("Caught: {!r}, returning failure.".format(e))

            exception_msg = re.sub(r"[\<\>]", "", e)
            return self._response(exception_msg, private=True, replace=False)

    def trigger(self, trigger_word, **kwargs):
        if not trigger_word:
            raise AttributeError("invalid invocation")

        kwargs.setdefauult("as_user", self.app.config["FLACK_DEFAULT_NAME"])

        def decorator(fn):
            logger.debug("Register trigger: {}".format(trigger_word))

            self.triggers[trigger_word] = SLACK_TRIGGER(
                callback=fn,
                user=kwargs["as_user"])

            return fn

        return decorator

    def command(self, name):
        if not name:
            raise AttributeError("invalid invocation")

        def decorator(fn):
            logger.debug("Register command: {}".format(name))
            self.commands[name] = fn
            return fn

        return decorator

    def action(self, name):
        if not name:
            raise AttributeError("invalid invocation")

        def decorator(fn):
            logger.debug("Register action: {}".format(name))
            self.actions[name] = fn
            return fn

        return decorator

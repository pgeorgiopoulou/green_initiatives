#!/usr/bin/env python3
"""Objects for votes and URLs. Allow collecting data, validating and searching for in database"""
# pylint: disable=fixme,redefined-outer-name

import base64
import json
from http import HTTPStatus

import flask
from flask import make_response, request
from flask_restful import Resource

from .databases.mysql_connect import MySQLHandler
from .templates.gi_types import Password
from .utils import get_logger

logger = get_logger()
m = MySQLHandler(logger)

session_cookie = "X-Session-Id"
reset_key = "YES I WANT TO REsET THE DB"
allowed_votes = {"up": 1, "down": -1}


class UserAPI(Resource):
    """@class managing user-related actions, such as login, logout, addition etc"""

    def post(self):
        """@brief HTTP POST handler for users

        Currently supported actions are:
            1. Login    Logs the user in, returns a session cookie
            2. Logout   Logs the user out, deletes the session relating to the session cookie
            3. Add      Adds new user to the system. Must be run by a user with sufficient permissions

        """
        path = request.path

        logger.debug(
            "method: %s, path: %s, data: %s, headers: %s, cookies: %s",
            request.method,
            request.path,
            request.get_data(),
            request.headers,
            request.cookies,
        )

        if path == "/login":
            return self._login(request)
        if path == "/logout":
            return self._logout(request)
        if path == "/add_user":
            return self._add_user(request)
        if path == "/delete_user":
            return self._delete_user(request)
        return make_response(
            "Not allowed to access resource or resource does not exist. See `/api/help` for more details\n",
            HTTPStatus.UNAUTHORIZED,
        )

    def _login(self, request: flask.Request) -> flask.Response:
        """@brief
        handles logging-in functionality and checks

        @param[in] request  Flask request object

        @return response    An HTTP response that can be returned by flask, using make_response
        """
        result = None

        _b64_credentials = request.headers.get("Authorization")
        if not _b64_credentials:
            return make_response("No credentials provided", HTTPStatus.BAD_REQUEST)
        username, password = base64.b64decode(_b64_credentials.removeprefix("Basic ")).decode().split(":")

        user_dictionary = m.get_user(username)
        logger.debug("User dictionary: %s", user_dictionary)

        if user_dictionary and user_dictionary[0].get("password", "") == Password(password).to_string():
            logger.debug("Creating session for user")
            result = m.add_session(username)
            logger.debug("Sending %d response with session_id %s in cookie", HTTPStatus.OK, result)
            response = make_response("", HTTPStatus.OK)
            response.set_cookie(session_cookie, result)

            return response

        return make_response("Invalid username or password", HTTPStatus.UNAUTHORIZED)

    def _logout(self, request: flask.Request) -> flask.Response:
        """@brief
        Handles logging-out functionality and checks

        @param[in] request  Flask request object

        @return response    An HTTP response that can be returned by flask, using make_response
        """
        cookie = request.cookies.get(session_cookie)
        if not cookie:
            return ("You're not logged in, can't log-out", HTTPStatus.UNAUTHORIZED)
        m.delete_session(cookie)
        # Always succeed
        return make_response("", HTTPStatus.OK)

    def _add_user(self, request: flask.Request) -> flask.Response:
        """@brief
        Handles functionality to add a user to the system

        @param[in] request  Flask request object

        @return response    An HTTP response that can be returned by flask, using make_response
        """
        cookie = request.cookies.get(session_cookie)

        data_string = request.data.decode()
        logger.debug("data_string: %s", data_string)
        data = json.loads(data_string)

        username = data["username"]
        password = data["password"]
        role = data["role"]
        result = m.add_user(username, password, role, cookie)
        response = make_response("", HTTPStatus.OK)
        if not result:
            response = make_response("Transaction failed", HTTPStatus.UNAUTHORIZED)
        return response

    def _delete_user(self, request: flask.Request) -> flask.Response:
        """@brief
        Handles functionality to delete a user from the system

        @param[in] request  Flask request object

        @return response    An HTTP response that can be returned by flask, using make_response
        """
        result = ""
        cookie = request.cookies.get(session_cookie)
        if not cookie:
            return ("You're not logged in, can't delete user", HTTPStatus.UNAUTHORIZED)

        data_string = request.data.decode()
        logger.debug("data_string: %s", data_string)
        data = json.loads(data_string)

        username = data["username"]
        result = m.delete_user(username, cookie)
        response = make_response("", HTTPStatus.OK)
        if not result:
            response = make_response("Transaction failed", HTTPStatus.UNAUTHORIZED)
        return response


class URLAPI(Resource):
    """@class Manages URL related actions, including add, remove (deactivate), list etc."""

    def post(self):
        """@brief HTTP POST function for URLS.

        Supported actions:
            1. Add URL
            2. GET specific URL (requires body with URL data)
            3. Delete URL -> Not using DELETE as it's actually a "set-inactive" function
        """
        logger.debug(
            "method: %s, path: %s, data: %s, headers: %s, cookies: %s",
            request.method,
            request.path,
            request.get_data(),
            request.headers,
            request.cookies,
        )

        cookie = request.cookies.get(session_cookie)
        data_string = request.data.decode()
        logger.debug("data_string: %s", data_string)
        path = request.path
        data = {}
        if data_string:
            data = json.loads(data_string)

        result = None
        if path == "/url/add":
            result = m.add_url(cookie, **data)
        if path == "/url/get":
            result = m.get_url(cookie, **data)
        if path == "/url/delete":
            request_data = {
                "field": "inactive",
                "value": True,
                "wherefield": "url",
                "wherevalue": data.get("url", "NO_SUCH_URL"),
            }
            result = m.set_url(cookie, **request_data)

        if not result:
            logger.info("Result was false, returning failure")
            return make_response("", HTTPStatus.BAD_REQUEST)
        logger.info("Result was True, returning success")
        return make_response(result, HTTPStatus.OK)

    def get(self):
        """@brief HTTP GET for URLs

        Supported actions:
            1. GET ALL Urls (Has no specifier)
        """
        logger.debug(
            "method: %s, path: %s, data: %s, headers: %s, cookies: %s",
            request.method,
            request.path,
            request.get_data(),
            request.headers,
            request.cookies,
        )
        data_string = request.data.decode()
        if data_string:
            json.loads(data_string)
        cookie = request.cookies.get(session_cookie)
        path = request.path
        result = None

        if path == "/url/getall":
            result = m.get_urls(cookie)

        if result is None:
            return make_response("", HTTPStatus.BAD_REQUEST)
        return make_response(result, HTTPStatus.OK)


class VoteAPI(Resource):
    """@class Manages voting, including casting votes"""

    def _set_vote(self, cookie, url, value):
        """@brief Sets the vote to a given value. Must be in allowed votes list

        @param[in]  cookie  The cookie used for authentication
        @param[in]  url     The URL to vote for
        @param[in]  value   The value to set the vote at

        @return response    A non-empty response in case of success
        """
        if value not in allowed_votes.values():
            return make_response(f"Bad vote value {value}", HTTPStatus.BAD_REQUEST)

        result = m.set_vote(cookie, value, url=url)
        if result:
            return make_response(result, HTTPStatus.OK)
        return make_response("", HTTPStatus.BAD_REQUEST)

    def _get_votes(self, cookie, url):
        """@brief Gets the sum of the votes to a given URL.

        @param[in]  cookie  The cookie used for authentication
        @param[in]  url     The URL to get the votes for

        @return response
        """

        result = m.get_votes(cookie, url=url)

        if result is None:
            return make_response("Not authorized to get votes for URL", HTTPStatus.UNAUTHORIZED)

        if not result:
            return make_response("Votes for URL not found", HTTPStatus.NOT_FOUND)

        return make_response(result[0], HTTPStatus.OK)

    def _get_all_votes(self, cookie):
        """@brief Gets the sum of the votes for all URLs

        @param[in]  cookie  The cookie used for authentication

        @return response
        """

        result = m.get_all_votes(cookie)

        if result is None:
            return make_response("Not authorized to get votes", HTTPStatus.UNAUTHORIZED)

        if not result:
            return make_response([], HTTPStatus.OK)

        return make_response(result, HTTPStatus.OK)

    def post(self, action=None):
        """@brief HTTP POST function for voting

        Supported actions:
            1. Set vote for specific URL
            2. Get vote for URL (need specific URL)
        """
        logger.debug(
            "method: %s, path: %s, data: %s, headers: %s, cookies: %s, action: %s",
            request.method,
            request.path,
            request.get_data(),
            request.headers,
            request.cookies,
            action,
        )
        if action not in allowed_votes.keys() and not action is None:
            return make_response(
                f"Unknown action {action}. Select one of {list(allowed_votes.keys())}",
                HTTPStatus.BAD_REQUEST,
            )

        cookie = request.cookies.get(session_cookie)
        path = request.path
        data_string = request.data.decode()
        data = json.loads(data_string)
        url = data.get("url")

        if not url:
            return make_response(
                f"URL not found in request",
                HTTPStatus.BAD_REQUEST,
            )

        if path.startswith("/vote/set/"):
            return self._set_vote(cookie, url, allowed_votes[action])

        if path.strip() == "/vote/get":
            return self._get_votes(cookie, url)

        return make_response(f"Invalid endpoint {path}", HTTPStatus.NOT_FOUND)

    def get(self):
        """@brief HTTP GET handler for Voting

        Supported actions:
            1. GET votes for all active URLs
        """
        logger.debug(
            "method: %s, path: %s, data: %s, headers: %s, cookies: %s",
            request.method,
            request.path,
            request.get_data(),
            request.headers,
            request.cookies,
        )
        cookie = request.cookies.get(session_cookie)
        path = request.path
        if path.strip() == "/vote/getall":
            return self._get_all_votes(cookie)


class HiddenAPI(Resource):
    """@class Handles actions that should be prohibited but are useful for testing. Adds minimal safeguards to avoid
    accidental launch"""

    def post(self):
        """@brief HTTP POST handler for hidden API

        Supported actions:
            1. reset_added_data Reset Database to default state (default users of each category, clean tables etc.)
        """
        path = request.path

        logger.debug(
            "method: %s, path: %s, data: %s, headers: %s, cookies: %s",
            request.method,
            request.path,
            request.get_data(),
            request.headers,
            request.cookies,
        )

        request.cookies.get(session_cookie)
        data_string = request.data.decode()
        logger.debug("data_string: %s", data_string)
        json.loads(data_string)

        if path == "/reset_added_data":
            return self._reset_added_data(request)
        return make_response(f"Invalid URL {path}", HTTPStatus.BAD_REQUEST)

    def get(self):
        """@brief HTTP GET handler for hidden API

        Supported actions:
            1. Get permissions for current user for all URLs
        """

        path = request.path

        logger.debug(
            "method: %s, path: %s, headers: %s, cookies: %s",
            request.method,
            request.path,
            request.headers,
            request.cookies,
        )

        cookie = request.cookies.get(session_cookie)
        logger.debug(cookie)  # MARKER

        if path.strip() == "/get_permissions":
            return self._get_permissions(cookie)
        if path.strip() == "/get_all_users":
            return self._get_all_users(cookie)
        if path.strip() == "/get_roles":
            return self._get_roles(cookie)

    def _get_permissions(self, cookie: str) -> flask.Response:
        """@brief Gets the permissions associated with this cookie

        @param[in]  cookie  String with the cookie of the user making the request
        """
        _permissions = m.get_all_permissions(cookie)
        if not _permissions:
            return make_response({}, HTTPStatus.UNAUTHORIZED)

        rolename = _permissions[0].get("rolename")
        username = _permissions[0].get("username")

        if not (rolename and username):
            return make_response({}, HTTPStatus.INTERNAL_SERVER_ERROR)

        permissions = {
            "role": rolename,
            "username": username,
            "permissions": {
                x["table"]: {"read": x["read"], "write": x["write"]} for x in _permissions if (x["read"] or x["write"])
            },
        }
        return make_response(permissions, HTTPStatus.OK)

    def _get_all_users(self, cookie: str) -> flask.Response:
        """@brief Gets all the users in the system

        @param[in]  cookie  String with the cookie of the user making the request
        """
        _users = m.get_all_users(cookie)
        if not _users:
            return make_response(
                "User retrieval failed, ensure user has the proper permissions",
                HTTPStatus.UNAUTHORIZED,
            )

        return make_response(_users, HTTPStatus.OK)

    def _get_roles(self, cookie: str) -> flask.Response:
        """@brief Gets all the roles known to the system

        @param[in]  cookie  String with the cookie of the user making the request
        """
        _roles = m.get_roles(cookie)
        if not _roles:
            return make_response(
                "User retrieval failed, ensure user has the proper permissions",
                HTTPStatus.UNAUTHORIZED,
            )

        return make_response(_roles, HTTPStatus.OK)

    def _reset_added_data(self, request: flask.Request) -> flask.Response:
        """@brief
        handles resetting of data such as urls and votes. Sessions and users remain unaffected.

        @param[in] request  Flask request object

        @return response    An HTTP response that can be returned by flask, using make_response
        """
        cookie = request.cookies.get(session_cookie)

        data_string = request.data.decode()
        logger.debug("data_string: %s", data_string)
        data = json.loads(data_string)

        if not data.get("key") == reset_key:
            response = make_response("Transaction failed", HTTPStatus.UNAUTHORIZED)
            return response

        result = m.reset_data(cookie)
        response = make_response("", HTTPStatus.OK)
        if not result:
            response = make_response("Transaction failed", HTTPStatus.UNAUTHORIZED)
        return response


# HTTP status codes:
# [<HTTPStatus.CONTINUE: 100>,
# <HTTPStatus.SWITCHING_PROTOCOLS: 101>,
# <HTTPStatus.PROCESSING: 102>,
# <HTTPStatus.EARLY_HINTS: 103>,

# <HTTPStatus.OK: 200>,
# <HTTPStatus.CREATED: 201>,
# <HTTPStatus.ACCEPTED: 202>,
# <HTTPStatus.NON_AUTHORITATIVE_INFORMATION: 203>,
# <HTTPStatus.NO_CONTENT: 204>,
# <HTTPStatus.RESET_CONTENT: 205>,
# <HTTPStatus.PARTIAL_CONTENT: 206>,
# <HTTPStatus.MULTI_STATUS: 207>,
# <HTTPStatus.ALREADY_REPORTED: 208>,
# <HTTPStatus.IM_USED: 226>,

# <HTTPStatus.MULTIPLE_CHOICES: 300>,
# <HTTPStatus.MOVED_PERMANENTLY: 301>,
# <HTTPStatus.FOUND: 302>,
# <HTTPStatus.SEE_OTHER: 303>,
# <HTTPStatus.NOT_MODIFIED: 304>,
# <HTTPStatus.USE_PROXY: 305>,
# <HTTPStatus.TEMPORARY_REDIRECT: 307>,
# <HTTPStatus.PERMANENT_REDIRECT: 308>,

# <HTTPStatus.BAD_REQUEST: 400>,
# <HTTPStatus.UNAUTHORIZED: 401>,
# <HTTPStatus.PAYMENT_REQUIRED: 402>,
# <HTTPStatus.FORBIDDEN: 403>,
# <HTTPStatus.NOT_FOUND: 404>,
# <HTTPStatus.METHOD_NOT_ALLOWED: 405>,
# <HTTPStatus.NOT_ACCEPTABLE: 406>,
# <HTTPStatus.PROXY_AUTHENTICATION_REQUIRED: 407>,
# <HTTPStatus.REQUEST_TIMEOUT: 408>,
# <HTTPStatus.CONFLICT: 409>,
# <HTTPStatus.GONE: 410>,
# <HTTPStatus.LENGTH_REQUIRED: 411>,
# <HTTPStatus.PRECONDITION_FAILED: 412>,
# <HTTPStatus.REQUEST_ENTITY_TOO_LARGE: 413>,
# <HTTPStatus.REQUEST_URI_TOO_LONG: 414>,
# <HTTPStatus.UNSUPPORTED_MEDIA_TYPE: 415>,
# <HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE: 416>,
# <HTTPStatus.EXPECTATION_FAILED: 417>,
# <HTTPStatus.IM_A_TEAPOT: 418>,
# <HTTPStatus.MISDIRECTED_REQUEST: 421>,
# <HTTPStatus.UNPROCESSABLE_ENTITY: 422>,
# <HTTPStatus.LOCKED: 423>,
# <HTTPStatus.FAILED_DEPENDENCY: 424>,
# <HTTPStatus.TOO_EARLY: 425>,
# <HTTPStatus.UPGRADE_REQUIRED: 426>,
# <HTTPStatus.PRECONDITION_REQUIRED: 428>,
# <HTTPStatus.TOO_MANY_REQUESTS: 429>,
# <HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE: 431>,
# <HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS: 451>,

# <HTTPStatus.INTERNAL_SERVER_ERROR: 500>,
# <HTTPStatus.NOT_IMPLEMENTED: 501>,
# <HTTPStatus.BAD_GATEWAY: 502>,
# <HTTPStatus.SERVICE_UNAVAILABLE: 503>,
# <HTTPStatus.GATEWAY_TIMEOUT: 504>,
# <HTTPStatus.HTTP_VERSION_NOT_SUPPORTED: 505>,
# <HTTPStatus.VARIANT_ALSO_NEGOTIATES: 506>,
# <HTTPStatus.INSUFFICIENT_STORAGE: 507>,
# <HTTPStatus.LOOP_DETECTED: 508>,
# <HTTPStatus.NOT_EXTENDED: 510>,
# <HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED: 511>]

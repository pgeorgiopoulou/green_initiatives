#!/usr/bin/env python3
# pylint: disable=fixme
"""Handlers for the green initiatives.

These are the classes, subclassing flask_restful.Resource, that are used in the API. Each class implements the HTTP
methods it will be serving
"""
from __future__ import annotations

from http import HTTPStatus

from flask import make_response, request
from flask_restful import Resource

from .datatypes import URLAPI, UserAPI, VoteAPI
from .utils import get_logger

logger = get_logger()

api_links = []

api_links.append(
    {
        "links": [
            {"endpoint": "/login", "help": "Login endpoint, used with POST"},
            {"endpoint": "/logout", "help": "Logout endpoint, used with POST"},
            {
                "endpoint": "/add_user",
                "help": "Endpoint to add user, used with POST. Must be logged-in with sufficient rights",
            },
            {
                "endpoint": "/delete_user",
                "help": "Endpoint to delete user, used with POST. Must be logged-in with sufficient rights",
            },
        ],
        "class": UserAPI,
    },
)

api_links.append(
    {
        "links": [
            {
                "endpoint": "/url/get",
                "help": "Get information on a URL, submitted with the `URL` field",
            },
            {"endpoint": "/url/getall", "help": "Get a list of all known URLs"},
            {"endpoint": "/url/delete", "help": "Delete a URL"},
            {
                "endpoint": "/url/add",
                "help": "Add a URL to the list. Must be logged-in with sufficient rights",
            },
        ],
        "class": URLAPI,
    },
)

api_links.append(
    {
        "links": [
            {
                "endpoint": "/vote/get",
                "help": "Get the votes on a URL. Must be used with POST, logged-in with sufficient rights",
            },
            {
                "endpoint": "/vote/getall",
                "help": "Get votes for all URLs. Used with GET",
            },
            {
                "endpoint": "/vote/set/<action>",
                "help": (
                    "Vote on a URL. Must be used with POST, while logged in, with the `URL` field set to a known URL"
                ),
            },
        ],
        "class": VoteAPI,
    },
)


class RefAPI(Resource):
    """@class   Returns a help message about the API"""

    api_links.append(
        {
            "links": [
                {"endpoint": "/api/help", "help": "Returns the API references"},
            ],
        },
    )

    def get(self):
        """@brief handles `get` requests"""
        if request.path == "/api/help":
            helper_list = {s["endpoint"]: s["help"] for s in [y for x in api_links for y in x["links"]]}
            logger.debug("helper_list: %s", helper_list)
            return make_response(helper_list)
        return make_response("", HTTPStatus.BAD_REQUEST)


api_links[-1]["class"] = RefAPI

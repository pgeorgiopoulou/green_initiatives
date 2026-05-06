#!/usr/bin/env python3
"""Implements the backend for the green-initiatives thesis

This is the entry point. Uses `flask` python module to facilitate the creation of an API easily
"""
from __future__ import annotations

import time
from http import HTTPStatus

from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from helpers.datatypes import HiddenAPI
from helpers.handlers import api_links
from helpers.utils import get_logger

app_name = "green-initiatives"
logger = get_logger()


def main():
    """Main function, encapsulates the workhorses"""
    app = Flask(app_name)
    CORS(app, supports_credentials=True, origins=["http://localhost:30080", "http://192.168.20.8:30080"])
    app.config["CORS_HEADERS"] = "Content-Type"
    api = Api(app)

    logger.debug("api_links: %s", api_links)

    for api_link in api_links:
        link_class = api_link["class"]
        links = [x["endpoint"] for x in api_link["links"]]
        logger.debug("Adding class %s for endpoints %s", link_class, links)

        api.add_resource(link_class, *links)
    api.add_resource(HiddenAPI, "/reset_added_data", "/get_all_users", "/get_permissions", "/get_roles")

    def respond_with_help(error):
        """@brief Error handler, allows 404 to return useful information"""
        return (
            "Unknown page, please refert to /api/help endpoint for a list of available sites\n",
            HTTPStatus.NOT_FOUND,
        )

    app.register_error_handler(HTTPStatus.NOT_FOUND, respond_with_help)
    app.run(debug=True, host="0.0.0.0", use_reloader=True)


if __name__ == "__main__":
    for i in range(10):
        try:
            main()
        except Exception:
            time.sleep(120)

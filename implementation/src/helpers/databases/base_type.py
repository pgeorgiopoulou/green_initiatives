#!/usr/bin/env python3
# mypy: disable-error-code="index, attr-defined, union-attr, arg-type"
"""The generic Database object, that abstracts the functions towards the database backend."""
# pylint: disable=super-init-not-called
from __future__ import annotations

import os
import typing

from ..templates.gi_types import VoteType

database_name = "green_initiatives"
# The MARIADB_ROOT_PASSWORD environment variable **must** be set for this to work. The target host is given as the
# container name
connection_data = {
    "user": "root",
    "password": os.environ["MARIADB_ROOT_PASSWORD"],
    "host": "database",
    "port": 3306,
}


class DatabaseObject:
    """@class   Base Class to inherit from. Forces a common language"""

    def __init__(self, logger):
        """@brief Initialises the database object

        @param[in]  logger  Logging object to use to report issues
        """
        raise NotImplementedError

    def __del__(self):
        """@brief Cleanup for the database object"""
        raise NotImplementedError

    def initialise(self, redo=False):
        """@brief Initialises the database

        @param[in]  redo  Whether re-initialisation should run on a non-empty DB
        """
        raise NotImplementedError

    def add_user(self, username: str, password: str, role: str, cookie: str) -> bool:
        """@brief Add user to the database

        @param[in]  username    The username to add
        @param[in]  password    The password to set for the user
        @param[in]  role        The user role
        @param[in]  cookie      The session cookie authenticating the user creating the new account

        @return boolean showing status of request
        """
        raise NotImplementedError

    def get_all_permissions(self, cookie: str) -> list:
        """@brief Get all permissions associated with the given cookie

        @param[in]  cookie      The session cookie authenticating the user creating the new account

        @return permissions List with all permissions by the user
        """
        raise NotImplementedError

    def delete_user(self, username: str, cookie: str) -> str:
        """@brief Delete user from the database

        @param[in]  username    The username to delete
        @param[in]  cookie      Session cookie for user making the call

        @return boolean showing status of request
        """
        raise NotImplementedError

    def get_user(self, username: str) -> dict[typing.Any, typing.Any]:
        """@brief Returns a user dictionary

        @param[in]  username    The username to add

        @return dictionary with user data
        """
        raise NotImplementedError

    def get_roles(self, cookie: str) -> List[str]:
        """@brief Get the names of all roles known to the system

        @param[in]  cookie      Session cookie for user making the call

        @return List of strings
        """
        raise NotImplementedError

    def get_all_users(self) -> list[dict[typing.Any, typing.Any]]:
        """@brief Returns a user dictionary

        @return list of dictionaries with user data
        """
        raise NotImplementedError

    def add_session(self, username: str) -> str | dict[typing.Any, typing.Any]:
        """@brief Add a user sesssion

        @param[in]  username     Username to add session for

        @return cookie or dictionary with more information
        """
        raise NotImplementedError

    def get_session(self, sessionid: str) -> dict[typing.Any, typing.Any]:
        """@brief Get the session, if available, for the current user

        @param[in]  sessionid    Session ID to get

        @return dictionary with session data
        """
        raise NotImplementedError

    def delete_session(self, sessionid: str):
        """@brief Remove the session, if available

        @param[in]  sessionid    Session ID to delete
        """
        raise NotImplementedError

    def add_url(self, cookie: str, title: str, url: str) -> str:
        """@brief Add URL to the database. The function stores the escaped version for both URL and Title

        @param[in]  referrer    The user adding the URL
        @param[in]  title       The title of the URL
        @param[in]  URL         The URL to add

        @return string as boolean boolean
        """
        raise NotImplementedError

    def get_url(self, cookie: str, /, **data: dict[str, typing.Any]) -> dict[typing.Any, typing.Any]:
        """@brief Returns a dictionary with the data of the URL

        @param[in]  cookie  Authentication cookie for which to
        @param[in]  data    Search data. Dictionary that must contain a.l. one of uid, url, title.

        @return dictionary with URL data
        """
        raise NotImplementedError

    def set_url(self, cookie: str, /, **data: dict[str, typing.Any]) -> dict[typing.Any, typing.Any] | bool | str:
        """@brief Returns a dictionary with the data of the URL

        @param[in]  cookie  The session cookie
        @param[in]  data    Dictionary with specific allowed keys, that allows updating a URL entry fields

        @return boolean     Success or failure status
        """
        raise NotImplementedError

    def set_vote(self, cookie: str, vote: VoteType, *, url: str = "", title: str = "") -> dict[typing.Any, typing.Any]:
        """@brief Sets the vote of a given user

        @param[in]  user    Username of voter
        @param[in]  vote    The user's vote
        @param[in]  url     URL to search for. If not set, title *MUST* be set
        @param[in]  title   Title to search for. If not set, URL *MUST* be set
        """
        raise NotImplementedError

    def get_all_votes(self, cookie: str) -> list[dict]:
        """@brief Get the votes for all URLs known to the system.

        @return list of dictionaries with URLs and their respective votes
        """
        raise NotImplementedError

    def get_vote(self, cookie: str, url: str) -> int or None:
        """@brief Get the sum of votes for a specific URL

        @param[in]  url     URL to get votes for. If not found in the system, the votes are none

        @return integer value as sum of votes or None to indicate URL not found
        """
        raise NotImplementedError

    def get_votes(self, cookie: str, url: str) -> int or None:
        """@brief Get the sum of votes for a specific URL

        @param[in]  url     URL to get votes for. If not found in the system, the votes are none

        @return integer value as sum of votes or None to indicate URL not found
        """

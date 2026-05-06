#!/usr/bin/env python3
# mypy: disable-error-code="index, attr-defined, union-attr, arg-type"
# pylint: disable=fixme
"""The MySQL database object handling class is defined in this file."""
# pylint: disable=super-init-not-called
from __future__ import annotations

import base64
import inspect
import json
import logging
import pathlib
import time
import typing
from copy import deepcopy

import mysql.connector

from ..templates import mysql_queries as _mysql_queries
from ..templates.gi_types import Password, VoteType
from .base_type import DatabaseObject, connection_data, database_name

mysql_queries = _mysql_queries.mysql_queries

base_dir = pathlib.Path(__file__).absolute().parent


def safe_relative_to(full_path: str, base_path: str) -> str:
    """@brief Returns the path relative to the full path, only if the base_path is a parent of the full path.

    @param[in] full_path    The full path
    @param[in] base_path    The parent path to trim off

    @return The trimmed path if applicable
    """
    return (
        str(pathlib.Path(full_path).relative_to(base_path))
        if pathlib.Path(full_path).is_relative_to(base_path)
        else full_path
    )


class MySQLHandler(DatabaseObject):
    """Class abstracting calls to MySQL server, wrapping `mysql-connector-python` module calls in simpler function
    calls
    """

    def __init__(self, logger: logging.Logger):
        """@brief Class constructor. Initialises a connection and a cursor object (type: dictionary)

        @param[in]  logger  Logging object to use to report issues
        """
        self.connection_data = deepcopy(connection_data)
        self._cnx_var = None
        self._cur_var = None
        self.logger = logger
        self.initialise()

    def __del__(self):
        """@brief Deconstructor, closes connection if not closed"""
        if not self._cnx.is_closed():
            self._cnx.close()

    @property
    def _cnx(self) -> mysql.connector.MySQLConnection:
        """@brief Getter for CNX property. Allows running command to force renewal if broken"""
        return self._renew_cnx()

    @property
    def initialised(self) -> bool:
        """@brief Getter for initialised value, returns true if the library exists"""
        # Duplicate, do not use self._execute() to avoid vicious loops
        try:
            self._cur.execute(query)
            resp = self._cur.fetchall()
            self._cnx.commit()
            return bool(resp)
        except Exception:
            return False

    @property
    def _cur(self) -> mysql.connector.cursor_cext.CMySQLCursor:
        """@brief Getter for CUR property. Allows running command to force renewal if broken"""
        return self._renew_cur()

    def _renew_cnx(self) -> mysql.connector.MySQLConnection:
        """@brief Renews Connector for MySQL server"""
        if self._cnx_var and self._cnx_var.is_connected():
            self._cnx_var.ping(reconnect=True)
            self.logger.debug("CNX established, reusing")
            return self._cnx_var

        self.logger.debug("Establishing CNX. type CNX: %s", type(self._cnx_var))
        self._cnx_var = mysql.connector.connect(**self.connection_data)
        self._cnx_var.start_transaction(isolation_level="READ COMMITTED")
        return self._cnx_var

    def _reset_connection(self) -> None:
        """@brief Resets the connection by closing and deleting the cursor and connection to the base"""
        self._cur_var.close()
        self._cur_var = None
        try:
            _ = self._cur_var.fetchall()
        except Exception:
            pass
        self._cnx_var.close()
        self._cnx_var = None

    def _renew_cur(self) -> mysql.connector.cursor_cext.CMySQLCursor:
        """@brief Renews cursor to use for commands"""
        if self._cur_var:
            return self._cur_var
        self._cur_var = self._cnx.cursor(dictionary=True)
        self.logger.debug("self.cur renewed. Contents: %s", self._cur_var)
        return self._cur_var

    def _execute(self, query: str, retries=3) -> dict[typing.Any, typing.Any]:
        """@brief Executes an SQL query, pythonizes the result and returns it

        @param[in]  query   Command to execute
        """
        caller = inspect.stack()[1]
        for attempt in range(retries):
            self.logger.debug(
                "Called from: [%s:%s:(%s)], attempt #%d Executing query '%s'",
                safe_relative_to(caller.filename, base_dir),
                caller.lineno,
                caller.function,
                attempt,
                query,
            )
            try:
                self._cur.execute(query)
                resp = self._cur.fetchall()
                self._cnx.commit()
                self.logger.debug("Response '%s'", resp)
                return resp
            except mysql.connector.errors.ProgrammingError as e:
                self.initialise()
            except mysql.connector.errors.IntegrityError as e:
                self.logger.warning("Got integrity error e: %s", e)
                return None
            except mysql.connector.errors.Error as e:
                self.logger.error("%s: %s", type(e), e)
                self._reset_connection()
        else:
            return {}

    def initialise(self, redo=False):
        """@brief Initialises the database"""
        if self.initialised and not redo:
            self.logger.warning("Already initialised, not redoing")
            return True

        # Add database
        self.logger.debug("Adding database %s", database_name)
        self._execute(mysql_queries["create_database"].format(database_name=database_name))
        # Add tables
        self.logger.debug("Adding tables in database")
        for create_table_query in mysql_queries["create_tables"]:
            self._execute(create_table_query.format(database_name=database_name))
        # Add default values in tables
        self.logger.debug("Populating tables with default values")
        for insert_query in mysql_queries["add_default_values"]:
            self._execute(insert_query.format(database_name=database_name))
        return True

    def _get_permissions(self, cookie: str, direction: str, table: str) -> list:
        """@brief Verify that the permissions list of dictionary has write for the table

        @param[in]  cookie      Session cookie for which permissions are checked
        @param[in]  direction   `read` / `write`, what type of permission is being validated
        @param[in]  table       Which table the user has the permissions on

        @return boolean     True if user has permissions, False if not
        """

        permissions = self.get_all_permissions(cookie)
        self.logger.debug("Got permissions for user: %s", json.dumps(permissions, indent=4))

        if not permissions:
            return []

        contained = list(filter(lambda x: x["table"] == table and x[direction], permissions))
        return contained

    def get_all_permissions(self, cookie: str) -> list:
        """@brief Verify that the permissions list of dictionary has write for the table

        @param[in]  cookie      Session cookie for which permissions are checked

        @return permissions List with all permissions by the user
        """
        query = mysql_queries["get_permissions"].format(cookie=cookie)
        permissions = self._execute(query)

        return permissions or []

    def reset_data(self, cookie: str) -> bool:
        """@brief Add user to the database

        @param[in]  cookie      The session cookie authenticating the user creating the new account

        @return boolean showing status of request
        """

        can_write_db = self._get_permissions(cookie, "write", "db")
        if not can_write_db:
            self.logger.error("User %s does not have write access to database", cookie)
            return False

        query = "DELETE FROM votes;"
        self._execute(query)
        query = "DELETE FROM urls;"
        self._execute(query)
        return True

    def add_user(self, username: str, password: str, role: str, cookie: str) -> bool:
        """@brief Add user to the database

        @param[in]  username    The username to add
        @param[in]  password    The password to set for the user
        @param[in]  role        The user role in string format. Must be valid, assume an admin knows the roles.
        @param[in]  cookie      The session cookie authenticating the user creating the new account

        @return boolean showing status of request
        """

        can_write_users = self._get_permissions(cookie, "write", "users")
        if not can_write_users:
            self.logger.error("User %s does not have write access to users table", cookie)
            return False

        query = mysql_queries["get_role_id"].format(role=role)
        role_numeric = self._execute(query)
        if not role_numeric:
            self.logger.error("Role %s does not correspond to a uid", role)
            return False
        role_numeric = role_numeric[0]["uid"]

        query = mysql_queries["add_user"].format(
            username=username,
            password=Password(password).to_string(),
            type=role_numeric,
        )
        role_numeric = self._execute(query)
        return True

    def delete_user(self, username: str, cookie: str) -> str:
        """@brief Delete user from the database

        @param[in]  username    The username to delete
        @param[in]  cookie      Session cookie for user making the call

        @return string-as-boolean showing status of request
        """
        all_permissions = self.get_all_permissions(cookie)

        user_permissions = [x for x in all_permissions if x["table"] == "users"]
        self.logger.debug("User permissions: %s", user_permissions)

        if not (user_permissions and user_permissions[0].get("write", 0)):
            self.logger.error("User %s does not have write access to users table", cookie)
            return ""
        if all_permissions[0]["username"] == username:
            self.logger.error("User %s cannot delete itself", username)
            return ""

        query = mysql_queries["delete_user"].format(username=username)
        self._execute(query)
        return "User Deleted"

    def get_user(self, username: str) -> dict[typing.Any, typing.Any]:
        """@brief Returns a user dictionary

        @param[in]  username    The username to get

        @return dictionary with user data
        """
        query = mysql_queries["search_user"].format(username=username)
        result = self._execute(query)
        self.logger.debug("Query %s returned %s", query, result)
        return result

    def get_roles(self, cookie: str) -> List[str]:
        """@brief Get the names of all roles known to the system

        @param[in]  cookie      Session cookie for user making the call

        @return List of strings
        """
        can_read_roles = self._get_permissions(cookie, "read", "roles")
        if not can_read_roles:
            self.logger.error("User %s does not have read access to roles table", cookie)
            return ""

        query = mysql_queries["get_roles"]
        result = self._execute(query)
        if not result:
            return ""

        return [x["name"] for x in result]

    def get_all_users(self, cookie) -> list[dict[typing.Any, typing.Any]]:
        """@brief Returns a user dictionary

        @param[in]  cookie      Session cookie for user making the call

        @return list of dictionaries with user data
        """
        can_read_users = self._get_permissions(cookie, "read", "users")
        if not can_read_users:
            self.logger.error("User %s does not have read access to users table", cookie)
            return {}

        query = mysql_queries["get_all_users"]
        result = self._execute(query)
        self.logger.debug("Query %s returned %s", query, result)
        return result

    def add_session(self, username: str) -> str | dict[typing.Any, typing.Any]:
        """@brief Add a user sesssion

        @param[in]  user     Username to add session for

        @return cookie or dictionary with SQL query response
        """
        timestamp = f"{time.time()}"
        session_string = f"{username}:{timestamp}"
        cookie = base64.b64encode(session_string.encode()).decode()

        query = mysql_queries["add_session"].format(username=username, cookie=cookie)
        result = self._execute(query)
        self.logger.debug("Query %s returned %s", query, result)
        return cookie or result

    def get_session(self, sessionid: str) -> dict[typing.Any, typing.Any]:
        """@brief Get the session, if available, for the current user

        @param[in]  sessionid    Session ID to get

        @return dictionary with session data
        """
        query = mysql_queries["get_session"].format(cookie=sessionid)
        result = self._execute(query)
        self.logger.debug("Got result %s", result)

        return result

    def delete_session(self, sessionid: str):
        """@brief Delete a session from the database

        @param[in]  sessionid    Session ID to delete
        """
        query = mysql_queries["delete_session"].format(cookie=sessionid)
        self._execute(query)

    def add_url(self, cookie: str, title: str, url: str) -> str:
        """@brief Add URL to the database. The function stores the escaped version for both URL and Title

        @param[in]  referrer    The user adding the URL
        @param[in]  title       The title of the URL
        @param[in]  URL         The URL to add

        @return status boolean
        """
        # TODO use the UPDATE DUPLICATE mechanism instead
        allowed = self._get_permissions(cookie, "write", "urls")

        if not allowed:
            return ""

        username = allowed[0]["username"]

        url_present = self.get_url(cookie, url=url, inactive=True)

        if url_present:
            if url_present[0].get("inactive") == 0:
                self.logger.debug("URL %s is already present on the system", url)
                return ""

            request_data = {
                "field": "inactive",
                "value": False,
                "wherefield": "url",
                "wherevalue": url,
            }
            self.set_url(cookie, **request_data)
            return "SUCCESS"

        query = mysql_queries["add_url"].format(url=url, title=title, referrer=username)
        result = self._execute(query)
        if result is None:
            return ""
        return "SUCCESS"

    def get_url(self, cookie: str, /, inactive=False, **data: dict[str, typing.Any]) -> dict[typing.Any, typing.Any]:
        """@brief Returns a dictionary with the data of the URL

        The fields for data are listed in order of priority in the param information below. There is no collision,
        because only one is used

        @param[in]  cookie  Authentication cookie for which to
        @param[in]  data    Search data. Dictionary that must contain a.l. one of uid, url, title.

        @return dictionary with URL data
        """
        caller = inspect.stack()[1]
        self.logger.debug(
            "Called from: [%s:%s:(%s)], params: {inactive: %s, data: %s}",
            safe_relative_to(caller.filename, base_dir),
            caller.lineno,
            caller.function,
            inactive,
            data,
        )

        allowed = self._get_permissions(cookie, "read", "urls")
        if not allowed:
            return {}

        _condition = [f"`{x}` = '{y}'" for x, y in data.items()]

        query_base = mysql_queries["get_url"] if not inactive else mysql_queries["get_url_including_inactive"]
        query = query_base.format(condition=" AND ".join(_condition))

        result = self._execute(query)
        if result is None:
            return {}

        if inactive:
            return result

        for x in result:
            del x["inactive"]
        return result

    def get_urls(self, cookie: str, /) -> dict[typing.Any, typing.Any]:
        """@brief Returns a dictionary with the data of all URLs

        The fields for data are listed in order of priority in the param information below. There is no collision,
        because only one is used

        @param[in]  cookie  Authentication cookie for which to

        @return list of dictionaries with URL data
        """
        allowed = self._get_permissions(cookie, "read", "urls")
        if not allowed:
            return {}

        query = mysql_queries["get_urls"]
        result = self._execute(query)
        if result is None:
            return False
        return result

    def set_url(self, cookie: str, /, **data: dict[str, typing.Any]) -> dict[typing.Any, typing.Any] | bool | str:
        """@brief Returns a dictionary with the data of the URL

        @param[in]  cookie  The session cookie
        @param[in]  data    Dictionary with specific allowed keys, that allows updating a URL entry fields

        @return boolean     Success or failure status
        """

        allowed = self._get_permissions(cookie, "write", "urls")
        if not allowed:
            return {}

        query = mysql_queries["set_url"].format(
            field=data["field"],
            value=data["value"],
            wherefield=data["wherefield"],
            wherevalue=data["wherevalue"],
        )
        result = self._execute(query)
        if result is None:
            return False
        return "SUCCESS"

    def set_vote(self, cookie: str, vote: VoteType, *, url: str = "", title: str = "") -> dict[typing.Any, typing.Any]:
        """@brief Sets the vote of a given user

        @param[in]  user    Username of voter
        @param[in]  vote    The user's vote
        @param[in]  url     URL to search for. If not set, title *MUST* be set
        @param[in]  title   Title to search for. If not set, URL *MUST* be set
        """

        allowed = self._get_permissions(cookie, "write", "votes")
        if not allowed:
            return {}

        voter = self.get_session(cookie)[0].get("user")

        query = mysql_queries["set_vote"].format(
            url=url,
            vote=vote,
            voter=voter,
        )
        result = self._execute(query)

        if result is None:
            return False
        return "SUCCESS"

    def get_all_votes(self, cookie: str) -> list[dict]:
        """@brief Get the votes for all URLs known to the system.

        @return list of dictionaries with URLs and their respective votes
        """
        allowed = self._get_permissions(cookie, "read", "votes")
        if not allowed:
            return None

        query = mysql_queries["get_all_votes"]
        result = self._execute(query)
        if result is None:
            return False

        for x in result:
            x["totalvotes"] = int(x["totalvotes"])
        return result

    def get_votes(self, cookie: str, url: str) -> int or None:
        """@brief Get the sum of votes for a specific URL

        @param[in]  url     URL to get votes for. If not found in the system, the votes are none

        @return integer value as sum of votes or None to indicate URL not found
        """
        allowed = self._get_permissions(cookie, "read", "votes")
        if not allowed:
            return None

        query = mysql_queries["get_url_votes"].format(
            url=url,
        )
        result = self._execute(query)

        if result is None:
            return False

        if result:
            result[0]["totalvotes"] = int(result[0]["totalvotes"])
        return result

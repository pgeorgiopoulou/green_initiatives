#!/usr/bin/env python3
# pylint: disable=fixme, redefined-outer-name, unused-argument
"""@file Conftest file, handling shared fixtures and hooks"""
import argparse
import importlib
import importlib.util
import logging
import pathlib
import sys
import typing

import pytest
import requests

src_base = list(pathlib.Path(__file__).resolve().parents)[1] / "src"

module_path = src_base / "helpers/utils.py"
module_name = "utils"
spec = importlib.util.spec_from_file_location(module_name, module_path.as_posix())
utils = importlib.util.module_from_spec(spec)  # type: ignore
sys.modules[module_name] = utils
spec.loader.exec_module(utils)  # type: ignore
reset_key = "YES I WANT TO REsET THE DB"

_lgr = utils.get_logger()


class SessionDict:
    """@class Contains a dictionary of sessions that get reused or closed and removed. Returns the appropriate session
    based on key provided"""

    def __init__(self):
        """@brief Initialiser class, no arguments"""
        self._sessions = {}
        self.logger = _lgr

    def session(self, session_name: str) -> requests.Session:
        """@brief Gets session based on name.

        @param[in]  session_name    The name of the session to return. Must be unique

        @return     session     The session with the given name. Create if not exist
        """
        s = self._sessions.get(session_name)
        if s:
            self.logger.debug("Session for %s found, returning", session_name)
            return s
        self.logger.debug("Session for %s NOT found, creating and returning", session_name)
        self._sessions[session_name] = requests.Session()
        return self._sessions[session_name]

    def close(self, session_name: str) -> None:
        """@brief Gets session based on name.

        @param[in]  session_name    The name of the session to return. Must be unique

        """
        self.logger.debug("Will attempt to close session for %s", session_name)
        s = self._sessions.get(session_name)
        if s:
            self.logger.debug("Session for %s found, closing", session_name)
            s.close()
            del self._sessions[session_name]


@pytest.fixture(scope="session")
def logger():
    """@brief Returns logger object for use where needed"""
    return _lgr


@pytest.fixture(scope="session")
def http_session():
    "Fixture returning a SessionDict to retrieve `request.Session` objects"
    return SessionDict()


cfg = argparse.Namespace()
cfg.url_base = "http://localhost:5000"
cfg.session_cookie = "X-Session-Id"

cfg.users = {
    "administrator": {"username": "administrator", "password": "administrator", "role": "administrator"},
    "moderator": {"username": "moderator", "password": "moderator", "role": "moderator"},
    "voter": {"username": "voter", "password": "voter", "role": "voter"},
    "reader": {"username": "reader", "password": "reader", "role": "reader"},
    "reader_one": {"username": "newreader", "password": "newreader", "role": "reader"},
    "reader_two": {"username": "readertwo", "password": "readertwo", "role": "reader"},
}

cfg.urls = {
    "unique": [
        {"url": "https://www.example1.com/url1", "title": "Unique title 1"},
        {"url": "https://www.example2.com/url2", "title": "Unique title 2"},
        {"url": "https://www.example3.com/url3", "title": "Unique title 3"},
        {"url": "https://www.example4.com/url4", "title": "Unique title 4"},
    ],
    "duplicate_title": [
        {"url": "https://www.example1.com/dupurl1", "title": "Duplicate Title 1"},
        {"url": "https://www.example2.com/dupurl2", "title": "Duplicate Title 1"},
    ],
    "same_base": [
        {"url": "https://www.example.com/base1/end1", "title": "Same base Title 1"},
        {"url": "https://www.example.com/base1/end2", "title": "Same base Title 2"},
    ],
    "absent": [
        {"url": "https://www.example.com/absent1", "title": "Absent URL 1"},
        {"url": "https://www.example.com/absent2", "title": "Absent URL 2"},
    ],
}


def login_user(session: requests.Session, username: str, password: str, lgr: logging.Logger) -> requests.Response:
    """@brief Handles the login of a username with a give username found in a configuration object

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  username    Username to login as
    @param[in]  password    Password to use to login
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug("Logging-in user %s with password %s", username, password)
    resp = session.post(f"{cfg.url_base}/login", auth=(username, password))
    return resp


def logout_user(session: requests.Session, lgr: logging.Logger) -> requests.Response:
    """@brief Handles the logout of the user who owns the session

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug("Logging-out user owning session %s", session)
    resp = session.post(f"{cfg.url_base}/logout")
    return resp


def add_url(
    session: requests.Session,
    url_data: dict[typing.Any, typing.Any],
) -> requests.Response:
    """@brief Handles the addition of URLs in the database

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  url_data    Data of the URL to add

    @return response    The response returned by the HTTP call
    """
    response = session.post(f"{cfg.url_base}/url/add", json=url_data)
    return response


def get_urls(
    session: requests.Session,
) -> requests.Response:
    """@brief Handles the retrieval of all URLs from the database

    @param[in]  session     HTTP session object, used to do the login

    @return response    The response returned by the HTTP call
    """
    response = session.get(f"{cfg.url_base}/url/getall")
    return response


def get_url(
    session: requests.Session,
    url_data: dict[typing.Any, typing.Any],
) -> requests.Response:
    """@brief Handles the retrieval of a specific url from the database

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  url_data    Data of the URL to retrieve

    @return response    The response returned by the HTTP call
    """
    response = session.post(f"{cfg.url_base}/url/get", json=url_data)
    return response


def delete_url(
    session: requests.Session,
    url: str,
) -> requests.Response:
    """@brief Handles the deletion of URLs (deactivation)

    Takes as an argument the exact URL to delete

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  url         The URL to remove, in string format. Must be FULL URL

    @return response    The response returned by the HTTP call
    """
    response = session.post(f"{cfg.url_base}/url/delete", json={"url": url})
    return response


def add_user(
    session: requests.Session,
    user_data: dict[typing.Any, typing.Any],
    lgr: logging.Logger,
) -> requests.Response:
    """@brief Handles the addition of user accounts

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  user_data   Data of the user to add
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug(
        "Adding user %s using cookie %s as authorization",
        user_data["username"],
        session.cookies.get(cfg.session_cookie),
    )
    response = session.post(f"{cfg.url_base}/add_user", json=user_data)
    return response


def delete_user(session, user_data, lgr):
    """@brief Handles the deletion of user accounts

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  user_data   Data of the user to add
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug(
        "Deleting user %s using cookie %s as authorization",
        user_data["username"],
        session.cookies.get(cfg.session_cookie),
    )
    response = session.post(f"{cfg.url_base}/delete_user", json={"username": user_data["username"]})
    return response


def upvote_url(session, url, lgr):
    """@brief Handles the upvoting of a given URL

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  url         The URL to upvote
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug(
        "Upvoting URL %s using cookie %s as authorization",
        url,
        session.cookies.get(cfg.session_cookie),
    )
    response = session.post(f"{cfg.url_base}/vote/set/up", json=url)
    return response


def downvote_url(session, url, lgr):
    """@brief Handles the upvoting of a given URL

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  url         The URL to upvote
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug(
        "Downvoting URL %s using cookie %s as authorization",
        url,
        session.cookies.get(cfg.session_cookie),
    )
    response = session.post(f"{cfg.url_base}/vote/set/down", json=url)
    return response


def get_url_votes(session, url, lgr):
    """@brief Handles the getting of the vote count for a given URL

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  url         The URL to get the votes for
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug(
        "Getting votes for URL %s using cookie %s as authorization",
        url,
        session.cookies.get(cfg.session_cookie),
    )
    response = session.post(f"{cfg.url_base}/vote/get", json=url)
    return response


def get_all_votes(session, lgr):
    """@brief Handles the getting of the vote count for all URLs

    @param[in]  session     HTTP session object, used to do the login
    @param[in]  lgr         Logger object to use for reporting

    @return response    The response returned by the HTTP call
    """
    lgr.debug(
        "Getting all URL votes using cookie %s as authorization",
        session.cookies.get(cfg.session_cookie),
    )
    response = session.get(f"{cfg.url_base}/vote/getall")
    return response


@pytest.fixture
def reset_db_data(logger) -> None:
    """@brief Resets the database contents so it always starts from a clean state

    @param[in]  lgr         Logger object to use for reporting
    """
    logger.debug("Re-initialising the database")
    session = requests.Session()
    resp = session.post(f"{cfg.url_base}/login", auth=("administrator", "administrator"))
    assert resp.ok, "Failed administrator login"
    resp = session.post(f"{cfg.url_base}/reset_added_data", json={"key": reset_key})
    assert resp.ok, "Failed database reset"


@pytest.fixture(scope="session")
def tst_configuration():
    """@brief Returns the configuration item"""
    return cfg


@pytest.fixture(scope="session")
def helpers():
    """@brief Contains Useful functions that perform core functionality"""
    helpers_obj = argparse.Namespace()
    helpers_obj.login = login_user
    helpers_obj.logout = logout_user
    helpers_obj.add_url = add_url
    helpers_obj.get_url = get_url
    helpers_obj.get_urls = get_urls
    helpers_obj.delete_url = delete_url
    helpers_obj.add_user = add_user
    helpers_obj.delete_user = delete_user
    helpers_obj.upvote_url = upvote_url
    helpers_obj.downvote_url = downvote_url
    helpers_obj.get_url_votes = get_url_votes
    helpers_obj.get_all_votes = get_all_votes
    return helpers_obj


@pytest.fixture(scope="class")
def get_admin_loginer(http_session, helpers, logger, tst_configuration):
    """@brief Return a function that allows logging-in the administrator user back-in after a logout"""

    def _admin_loginer():
        logger.debug("Logging in user administrator")
        session = http_session.session("administrator")
        user = tst_configuration.users["administrator"]
        return helpers.login(session, user["username"], user["password"], logger)

    return _admin_loginer


@pytest.fixture(scope="class")
def login_administrator(get_admin_loginer, logger):
    """@brief Handles the logging-in of the administrator user"""
    return get_admin_loginer()


@pytest.fixture(scope="class")
def login_moderator(http_session, helpers, logger, tst_configuration):
    """@brief Handles the logging-in of the administrator user"""
    logger.debug("Logging in user moderator")
    session = http_session.session("moderator")
    user = tst_configuration.users["moderator"]
    return helpers.login(session, user["username"], user["password"], logger)


@pytest.fixture(scope="class")
def get_admin_logouter(login_administrator, http_session, helpers, logger):
    """@brief Return a function that allows logging-out the administrator"""

    def _admin_logouter():
        """@brief Handles the logging-in of the administrator user"""
        session = http_session.session("administrator")
        result = helpers.logout(session, logger)
        http_session.close("administrator")
        return result

    return _admin_logouter


@pytest.fixture(scope="class")
def logout_administrator(get_admin_logouter):
    """@brief Handles the logging-out of the administrator user"""
    return get_admin_logouter()


@pytest.fixture(scope="class")
def login_voter(http_session, helpers, logger, tst_configuration):
    """@brief Handles the logging-in of the voter user"""
    logger.debug("Logging in user voter")
    session = http_session.session("voter")
    user = tst_configuration.users["voter"]
    return helpers.login(session, user["username"], user["password"], logger)


@pytest.fixture(scope="class")
def login_reader(http_session, helpers, logger, tst_configuration):
    """@brief Handles the logging-in of the administrator user"""
    logger.debug("Logging in user reader")
    session = http_session.session("reader")
    user = tst_configuration.users["reader"]
    yield helpers.login(session, user["username"], user["password"], logger)
    http_session.close("reader")


@pytest.fixture
def add_first_unique_url_as_administrator(
    helpers,
    tst_configuration,
    http_session,
    login_administrator,
):
    """@brief Adds the first URL as administrator"""
    session = http_session.session("administrator")
    urls = tst_configuration.urls
    return helpers.add_url(session, urls["unique"][0])


@pytest.fixture
def add_first_unique_url_as_logged_out_administrator(
    helpers,
    tst_configuration,
    http_session,
    logout_administrator,
):
    """@brief Adds the first URL as administrator"""
    session = http_session.session("administrator")
    urls = tst_configuration.urls
    return helpers.add_url(session, urls["unique"][0])


@pytest.fixture
def add_first_unique_url_as_moderator(
    helpers,
    tst_configuration,
    http_session,
    login_moderator,
):
    """@brief Adds the first URL as moderator"""
    session = http_session.session("moderator")
    urls = tst_configuration.urls
    return helpers.add_url(session, urls["unique"][0])


@pytest.fixture
def add_first_unique_url_as_voter(
    helpers,
    tst_configuration,
    http_session,
    login_voter,
):
    """@brief Adds the first URL as voter"""
    session = http_session.session("voter")
    urls = tst_configuration.urls
    return helpers.add_url(session, urls["unique"][0])


@pytest.fixture
def add_first_unique_url_as_reader(
    helpers,
    tst_configuration,
    http_session,
    login_reader,
):
    """@brief Adds the first URL as reader"""
    session = http_session.session("reader")
    urls = tst_configuration.urls
    return helpers.add_url(session, urls["unique"][0])


@pytest.fixture
def add_first_unique_url_as_anonymous(
    helpers,
    tst_configuration,
    http_session,
    login_reader,
):
    """@brief Adds the first URL as reader"""
    session = http_session.session("anonymous")
    urls = tst_configuration.urls
    return helpers.add_url(session, urls["unique"][0])


@pytest.fixture
def add_all_unique_urls_as_administrator(
    logger,
    helpers,
    tst_configuration,
    http_session,
    login_administrator,
):
    """@brief Adds all unique URLs as administrator"""
    session = http_session.session("administrator")
    urls = tst_configuration.urls

    logger.debug("Adding all unique URLs")
    return [helpers.add_url(session, url) for url in urls["unique"]]


@pytest.fixture
def add_all_duplicate_title_urls_as_administrator(
    helpers,
    tst_configuration,
    http_session,
    login_administrator,
):
    """@brief Adds all URLs with duplicate titles as administrator"""
    session = http_session.session("administrator")
    urls = tst_configuration.urls

    return [helpers.add_url(session, url) for url in urls["duplicate_title"]]


@pytest.fixture
def remove_url_as_administrator(
    logger,
    add_first_unique_url_as_administrator,
    helpers,
    tst_configuration,
    http_session,
):
    """@brief Remove a URL as administrator.

    @return Dictionary, with values removed URL and response (list of URLs found in system after the deletion)
    """
    session = http_session.session("administrator")
    response = helpers.get_urls(session)
    assert response.ok, "The request failed"

    expected_url = tst_configuration.urls["unique"][0]
    urls_in_system = response.json()
    assert expected_url["url"] in [x["url"] for x in urls_in_system], "The expected URL is not found in the response"

    helpers.delete_url(session, expected_url["url"])
    response = helpers.get_urls(session)
    assert response.ok, "The request failed"
    return {"expected_url": expected_url, "response": response}


@pytest.fixture
def remove_url_as_moderator(logger, add_first_unique_url_as_moderator, helpers, tst_configuration, http_session):
    """@brief As moderator, remove URL added as moderator"""
    assert add_first_unique_url_as_moderator.ok, "Addition of the URL failed"
    session = http_session.session("moderator")
    url = tst_configuration.urls["unique"][0]

    helpers.delete_url(session, url["url"])

    response = helpers.get_urls(session)
    assert response.ok, "The deletion failed"
    return {"expected_url": url, "response": response}

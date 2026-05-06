#!/usr/bin/env python3
# pylint: disable=too-many-arguments,unused-argument,too-many-positional-arguments
"""@file implements tests for the user api

Actions and tests:
    * login
        [x] Login successful for administrator
        [x] Login successful for newly added user
    * logout
        [x] Logout successful for administrator
        [x] Logout succesful for newly added user
    * add user
        [x] Admin (OK)
        [x] Non-administrator (FAIL)
        [x] Admin post-logout (FAIL)
        [x] Anonymous (FAIL)
    * remove user
        [x] Admin (OK)
        [x] Non-administrator (FAIL)
        [x] Admin post-logout (FAIL)
        [x] Anonymous (FAIL)
"""
from http import HTTPStatus

import pytest


class TestUserApiLoginLogout:
    """@class Tests the login / logout User API"""

    def test_login_administrator(self, login_administrator, tst_configuration, logger):
        """@brief verify that the user login succeeds for user administrator"""

        assert login_administrator.ok, logger.error(
            "Logging-in administrator failed, response was %s, %s",
            login_administrator.status_code,
            login_administrator.text,
        )
        assert login_administrator.cookies.get(tst_configuration.session_cookie), logger.error(
            "Session cookie not found in administrator session",
        )

    def test_logout_administrator(self, logout_administrator, logger):
        """@brief tests that administrator logout returns expected code"""
        assert logout_administrator.ok, logger.error("Logging-out administrator failed")


class TestUserAdd:
    """@class Tests the User creation API"""

    def test_admin_add_user_ok(self, login_administrator, helpers, http_session, logger, tst_configuration):
        """@brief verify that the new user is succesfully created, logged in and logged-out"""
        admin_session = http_session.session("administrator")
        user = tst_configuration.users["reader_one"]

        add_new_reader_user = helpers.add_user(admin_session, user, logger)
        assert add_new_reader_user.ok, logger.error(
            "Failed creating new user, response was %s, %s",
            add_new_reader_user.status_code,
            add_new_reader_user.text,
        )
        user_session = http_session.session(user["username"])
        login_new_reader_user = helpers.login(user_session, user["username"], user["password"], logger)
        assert login_new_reader_user.ok, logger.error(
            "Failed to log the new user in, response was %s, %s",
            login_new_reader_user.status_code,
            login_new_reader_user.text,
        )
        logout_new_reader_user = helpers.logout(user_session, logger)
        assert logout_new_reader_user.ok, logger.error(
            "Failed to log the new user out, response was %s, %s",
            logout_new_reader_user.status_code,
            logout_new_reader_user.text,
        )
        helpers.delete_user(admin_session, user, logger)
        http_session.close(user["username"])

    @pytest.mark.negative
    def test_user_create_fail_without_login(self, http_session, logger, helpers, tst_configuration):
        """@brief Verify that without an active login, a new user can't be created"""
        nologin_session = http_session.session("no_login")
        user = tst_configuration.users["reader_two"]
        resp = helpers.add_user(nologin_session, user, logger)
        try:
            assert resp.status_code == HTTPStatus.UNAUTHORIZED, logger.error(
                "User creation was allowed without an active session",
            )
        except Exception as e:
            logger.error("Exception %s:%s", type(e), e)
            raise
        finally:
            http_session.close("no_login")

    @pytest.mark.negative
    def test_admin_logged_out_user_create_fail(
        self,
        http_session,
        logout_administrator,
        logger,
        tst_configuration,
        helpers,
    ):
        """@brief Verify that after logout, the administrator session can no longer create users"""
        admin_session = http_session.session("administrator")
        assert logout_administrator.ok, logger.error("Admin user has not been logged out")

        user = tst_configuration.users["reader_two"]

        resp = helpers.add_user(admin_session, user, logger)
        try:
            assert resp.status_code == HTTPStatus.UNAUTHORIZED, logger.error(
                "User deletion was allowed without an active session",
            )
        except Exception:
            logger.error("User creation succeeded when it shouldn't")
            resp = helpers.delete_user(admin_session, user, logger)
            raise

    @pytest.mark.negative
    def test_verify_non_admin_user_create_fail(
        self,
        logger,
        login_administrator,
        login_reader,
        http_session,
        tst_configuration,
        helpers,
    ):
        """@brief verify that a non-administrator user cannot create a new user"""
        admin_session = http_session.session("administrator")
        reader_session = http_session.session("reader")
        user = tst_configuration.users["reader_two"]

        resp = helpers.add_user(reader_session, user, logger)
        try:
            assert resp.status_code == HTTPStatus.UNAUTHORIZED, logger.error(
                "User creation was allowed for a non-administrator user",
            )
        except Exception:
            logger.error("User creation succeeded when it shouldn't")
            resp = helpers.delete_user(admin_session, user, logger)
            raise


class TestUserDelete:
    """@class Test deletion of users. Most tests negative as deletion is tested on the setup / teardown for other tests
    level
    """

    @pytest.mark.negative
    def test_user_delete_fail_without_login(
        self,
        http_session,
        login_administrator,
        logger,
        tst_configuration,
        helpers,
    ):
        """@brief Verify that without an active login, a user can't be deleted"""
        admin_session = http_session.session("administrator")
        nologin_session = http_session.session("no_login")

        user = tst_configuration.users["reader_two"]
        resp = helpers.add_user(admin_session, user, logger)

        assert resp.ok, logger.error("Failed to created the new user via administrator")

        resp = helpers.delete_user(nologin_session, user, logger)
        assert resp.status_code == HTTPStatus.UNAUTHORIZED, logger.error(
            "User deletion was allowed without an active session",
        )

        resp = helpers.delete_user(admin_session, user, logger)
        if not resp.ok:
            logger.error("Failed to delete the new user as administrator, may need to remove manually")
            http_session.close("no_login")

    @pytest.mark.negative
    def test_verify_non_admin_user_delete_fail(
        self,
        http_session,
        login_administrator,
        login_reader,
        logger,
        tst_configuration,
        helpers,
    ):
        """@brief Verify that without an active login, a user can't be deleted"""
        admin_session = http_session.session("administrator")
        reader_session = http_session.session("reader")
        user = tst_configuration.users["reader_two"]

        resp = helpers.add_user(admin_session, user, logger)
        assert resp.ok, logger.error("Failed to created the new user via administrator")

        resp = helpers.delete_user(reader_session, user, logger)
        assert resp.status_code == HTTPStatus.UNAUTHORIZED, logger.error(
            "User deletion was allowed for non-administrator user",
        )

        resp = helpers.delete_user(admin_session, user, logger)
        if not resp.ok:
            logger.error("Failed to delete the new user as administrator, may need to remove manually")
            http_session.close("no_login")

    @pytest.mark.negative
    def test_verify_admin_user_cannot_delete_self(
        self,
        http_session,
        login_administrator,
        logger,
        tst_configuration,
        helpers,
    ):
        """@brief Verify that without an active login, a user can't be deleted"""
        admin_session = http_session.session("administrator")
        user = tst_configuration.users["administrator"]

        resp = helpers.delete_user(admin_session, user, logger)
        assert resp.status_code == HTTPStatus.UNAUTHORIZED, logger.error(
            "Administrator was allowed to delete itself",
        )

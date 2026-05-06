#!/usr/bin/env python3
"""@file Handles testing for URL API"""
# pylint: disable=fixme, unused-argument, redefined-outer-name, too-many-arguments,too-many-positional-arguments
import pytest

# pylint: disable=pointless-string-statement
""" @file implements tests for the URL api

Actions and tests:
    [x] Add URL
        [x] As administrator
            [x] Valid addition of single URL
            [x] Valid addition of multipel URLs
            [x] Duplicate Title, different URL
            [x] NEG Duplicate URL
        [x] As moderator
        [x] NEG As voter
        [x] NEG As reader
        [x] NEG As anonymous
        [x] NEG As administrator after logout
    [x] Get URL
        [x] All, as reader
        [x] Specific using URL, as reader
        [x] Specific using title, as reader
        [x] NEG As anonymous
        [x] NEG As administrator after logout
"""
compare_fields = ["url", "title"]


@pytest.mark.usefixtures("reset_db_data")
class TestAddURL:
    """@brief Test addtion of URLs functionality"""

    def test_verify_admin_add_single_url(
        self,
        logger,
        login_administrator,
        add_first_unique_url_as_administrator,
    ):
        """@brief Validate that a URL can be added from administrator user"""

        assert add_first_unique_url_as_administrator.ok, logger.error(
            "Failed to add the first regular URL: %s:%s",
            add_first_unique_url_as_administrator.status_code,
            add_first_unique_url_as_administrator.text,
        )

    def test_verify_admin_add_multiple_unique(self, logger, add_all_unique_urls_as_administrator):
        """@brief Validate that multiple URLs can be added from administrator user"""

        assert all(x.ok for x in add_all_unique_urls_as_administrator), logger.error(
            "Addition of some URLs failed: %s",
            [
                (resp.request.url, resp.request.headers, resp.request.body)
                for resp in add_all_unique_urls_as_administrator
                if not resp.ok
            ],
        )

    def test_verify_admin_add_duplicate_title(self, logger, add_all_duplicate_title_urls_as_administrator):
        """@brief Validate that a URL can be added from administrator user"""
        assert all(x.ok for x in add_all_duplicate_title_urls_as_administrator), logger.error(
            "Addition of some URLs failed: %s",
            [
                (resp.request.url, resp.request.headers, resp.request.body)
                for resp in add_all_duplicate_title_urls_as_administrator
                if not resp.ok
            ],
        )

    def test_verify_admin_add_same_base_urls(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_administrator,
    ):
        """@brief Validate that a URL can be added from administrator user if the base is the same, but not the entire URL"""
        session = http_session.session("administrator")
        urls = tst_configuration.urls

        add_all_same_base_urls_as_administrator = [helpers.add_url(session, url) for url in urls["same_base"]]

        assert all(x.ok for x in add_all_same_base_urls_as_administrator), logger.error(
            "Addition of some URLs failed: %s",
            [
                (resp.request.url, resp.request.headers, resp.request.body)
                for resp in add_all_same_base_urls_as_administrator
                if not resp.ok
            ],
        )

    def test_verify_admin_cannot_add_duplicate_url(
        self,
        add_all_unique_urls_as_administrator,
        logger,
        helpers,
        http_session,
        tst_configuration,
    ):
        """@brief Validate that URLs cannot be added if they're already in the base"""

        session = http_session.session("administrator")
        urls = tst_configuration.urls

        assert all(x.ok for x in add_all_unique_urls_as_administrator), logger.error(
            "Addition of some URLs failed: %s",
            [
                (resp.request.url, resp.request.headers, resp.request.body)
                for resp in add_all_unique_urls_as_administrator
                if not resp.ok
            ],
        )

        logger.debug("Trying to re-add all unique URLs")
        results = [helpers.add_url(session, url) for url in urls["unique"]]

        assert not any(x.ok for x in results), logger.error(
            "At least one URL was added successfully: %s",
            [(resp.request.url, resp.request.headers, resp.request.body) for resp in results if not resp.ok],
        )

    def test_verify_moderator_add_single_url(
        self,
        logger,
        login_moderator,
        add_first_unique_url_as_moderator,
    ):
        """@brief Validate that a URL can be added from moderator user"""

        assert add_first_unique_url_as_moderator.ok, logger.error(
            "Failed to add the first regular URL: %s:%s",
            add_first_unique_url_as_moderator.status_code,
            add_first_unique_url_as_moderator.text,
        )

    def test_verify_voter_cannot_add_url(
        self,
        logger,
        login_reader,
        add_first_unique_url_as_voter,
    ):
        """@brief Validate that a URL cannot be added from reader user"""

        assert not add_first_unique_url_as_voter.ok, logger.error(
            "Succeeded in adding a URL as voter: %s:%s",
            add_first_unique_url_as_reader.status_code,
            add_first_unique_url_as_reader.text,
        )

    def test_verify_reader_cannot_add_url(
        self,
        logger,
        login_reader,
        add_first_unique_url_as_reader,
    ):
        """@brief Validate that a URL cannot be added from reader user"""

        assert not add_first_unique_url_as_reader.ok, logger.error(
            "Succeeded in adding a URL as reader: %s:%s",
            add_first_unique_url_as_reader.status_code,
            add_first_unique_url_as_reader.text,
        )

    def test_verify_anonymous_cannot_add_url(
        self,
        logger,
        login_reader,
        add_first_unique_url_as_anonymous,
    ):
        """@brief Validate that a URL cannot be added from reader user"""

        assert not add_first_unique_url_as_anonymous.ok, logger.error(
            "Succeeded in adding a URL as reader: %s:%s",
            add_first_unique_url_as_anonymous.status_code,
            add_first_unique_url_as_anonymous.text,
        )

    def test_verify_logged_out_admin_cannot_add_test(
        self,
        logger,
        add_first_unique_url_as_logged_out_administrator,
    ):
        """@brief Validate that a URL cannot be added from reader user"""

        assert not add_first_unique_url_as_logged_out_administrator.ok, logger.error(
            "Succeeded in adding a URL as reader: %s:%s",
            add_first_unique_url_as_logged_out_administrator.status_code,
            add_first_unique_url_as_logged_out_administrator.text,
        )


@pytest.mark.usefixtures("reset_db_data")
class TestGetURL:
    """@brief Test getting of URL info functionality"""

    def test_verify_get_urls_as_voter(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_voter,
        add_all_unique_urls_as_administrator,
    ):
        """Check that all URLs can be retrieved"""
        reader_sesssion = http_session.session("voter")
        response = helpers.get_urls(reader_sesssion)
        assert response.ok, "The request failed"
        added_urls = response.json()
        logger.debug("URLs added in system: '''%s'''", added_urls)
        _added_urls_tuples = tuple(tuple(sorted(x.items())) for x in added_urls)
        logger.debug("URLs added in system, tuples format: '''%s'''", _added_urls_tuples)
        _configuration_urls_tuples = tuple(tuple(sorted(x.items())) for x in tst_configuration.urls["unique"])
        logger.debug("Original URLs in tuple format: '''%s'''", _configuration_urls_tuples)
        urls_diff = set(_added_urls_tuples).symmetric_difference(set(_configuration_urls_tuples))
        assert not urls_diff, (
            f"There are differences between the original ```{_added_urls_tuples}```"
            f" and returned ```{_configuration_urls_tuples}``` URL lists"
        )

    def test_verify_get_urls_as_reader(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_reader,
        add_all_unique_urls_as_administrator,
    ):
        """Check that all URLs can be retrieved"""
        reader_sesssion = http_session.session("reader")
        response = helpers.get_urls(reader_sesssion)
        assert response.ok, "The request failed"
        added_urls = response.json()
        logger.debug("URLs added in system: '''%s'''", added_urls)
        _added_urls_tuples = tuple(tuple(sorted(x.items())) for x in added_urls)
        logger.debug("URLs added in system, tuples format: '''%s'''", _added_urls_tuples)
        _configuration_urls_tuples = tuple(tuple(sorted(x.items())) for x in tst_configuration.urls["unique"])
        logger.debug("Original URLs in tuple format: '''%s'''", _configuration_urls_tuples)
        urls_diff = set(_added_urls_tuples).symmetric_difference(set(_configuration_urls_tuples))
        assert not urls_diff, (
            f"There are differences between the original ```{_added_urls_tuples}```"
            f" and returned ```{_configuration_urls_tuples}``` URL lists"
        )

    def test_verify_get_url_as_reader_by_url_unique_instance(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_reader,
        add_all_unique_urls_as_administrator,
    ):
        """Check that specific urls can be retrieved by URL"""
        reader_sesssion = http_session.session("reader")
        sample_url = tst_configuration.urls["unique"][0]
        response = helpers.get_url(reader_sesssion, {"url": sample_url["url"]})
        assert response.ok, "The request failed"
        response_url = response.json()[0]
        assert response_url["url"] == sample_url["url"], "The returned and original URLs' `url` fields do not match"
        assert (
            response_url["title"] == sample_url["title"]
        ), "The returned and original URLs' `title` fields do not match"

    def test_verify_get_url_as_reader_by_title_unique_instance(
        self,
        helpers,
        tst_configuration,
        http_session,
        login_reader,
        add_all_unique_urls_as_administrator,
    ):
        """@brief Verify reader can get URLs using unique title"""
        reader_sesssion = http_session.session("reader")
        sample_url = tst_configuration.urls["unique"][0]
        response = helpers.get_url(reader_sesssion, {"title": sample_url["title"]})
        assert response.ok, "The request failed"
        response_url = response.json()[0]
        assert response_url["url"] == sample_url["url"], "The returned and original URLs' `url` fields do not match"
        assert (
            response_url["title"] == sample_url["title"]
        ), "The returned and original URLs' `title` fields do not match"

    def test_verify_get_url_as_reader_by_title_duplicate_instance(
        self,
        helpers,
        tst_configuration,
        http_session,
        login_reader,
        add_all_duplicate_title_urls_as_administrator,
    ):
        """@brief Verify reader can get URLs using unique title"""
        reader_sesssion = http_session.session("reader")
        reference_urls = tst_configuration.urls["duplicate_title"]
        sample_url = reference_urls[0]
        response = helpers.get_url(reader_sesssion, {"title": sample_url["title"]})
        assert response.ok, "The request failed"
        response_urls = response.json()
        assert len(response_urls) == len(reference_urls), (
            f"Returned a list with incompatible number of elements: {response_urls}" f" VS {reference_urls}"
        )
        assert all(
            x["title"] == reference_urls[0]["title"] for x in response_urls
        ), f"Some of the returned values have a different title to the one being searched-for: {response_urls}"

    def test_verify_get_url_as_anonymous_fails(
        self,
        helpers,
        tst_configuration,
        http_session,
        add_all_unique_urls_as_administrator,
    ):
        """@brief Verify that anonymous user has no read access"""
        session = http_session.session("anonymous")
        sample_url = tst_configuration.urls["unique"][0]
        response = helpers.get_url(session, {"title": sample_url["title"]})
        assert not response.ok, "The request succeeded for anonymous user. It shouldn't"

    def test_verify_get_url_as_logged_out_admin_fails(
        self,
        helpers,
        tst_configuration,
        http_session,
        logout_administrator,
        add_all_unique_urls_as_administrator,
    ):
        """@brief Verify that after logout, administrator has no longer read access"""
        session = http_session.session("administrator")
        sample_url = tst_configuration.urls["unique"][0]
        response = helpers.get_url(session, {"title": sample_url["title"]})
        assert not response.ok, "The request succeeded for administrator post-logout. It shouldn't"


@pytest.mark.usefixtures("reset_db_data")
class TestModifyURL:
    """@brief Test modification of URLs functionality

    Features
    =========
    * Deactivate URL
    * Reactivate URL
    * Re-adding de-activated not allowed

    Tests
    =====
    * [x] As administrator
        * [x] Valid modification
        * [] NEG Prohibited field - N/A
    * [x] As moderator
        * [x] Remove URL previously added by moderator
        * [x] Add URL previously removed by moderator
        * [x] Remove URL previously added by administrator
        * [x] Add URL previously removed by administrator
    """

    def test_verify_admin_can_deactivate_url(
        self,
        logger,
        remove_url_as_administrator,
        helpers,
        tst_configuration,
        http_session,
    ):
        """@brief Verify administrator can de-activate a URL"""

        urls_in_system = remove_url_as_administrator["response"].json()
        expected_url = remove_url_as_administrator["expected_url"]
        assert expected_url["url"] not in [
            x["url"] for x in urls_in_system
        ], f"The deleted URL {expected_url} is still found in the response"

    def test_verify_admin_can_reactivate_url(
        self,
        logger,
        remove_url_as_administrator,
        helpers,
        tst_configuration,
        http_session,
    ):
        """@brief Verify administrator can re-activate a URL. To do so, the URL gets added"""

        # Verify that the removal worked
        urls_in_system = remove_url_as_administrator["response"].json()
        expected_url = remove_url_as_administrator["expected_url"]
        assert expected_url["url"] not in [
            x["url"] for x in urls_in_system
        ], f"The deleted URL {expected_url} is still found in the response"

        session = http_session.session("administrator")
        response = helpers.add_url(session, expected_url)
        assert response.ok, f"The addition of URL {expected_url} failed"

        response = helpers.get_urls(session)
        assert response.ok, "Getting the URLs failed"

        urls_in_system = response.json()

        assert expected_url["url"] in [
            x["url"] for x in urls_in_system
        ], f"The re-added URL {expected_url} is still not found in the response"

    def test_verify_moderator_can_delete_url_added_by_moderator(
        self,
        logger,
        helpers,
        tst_configuration,
        remove_url_as_moderator,
        http_session,
    ):
        """@brief Verify that moderator can delete a URL added by a moderator"""
        http_session.session("moderator")

        url, response = remove_url_as_moderator["expected_url"], remove_url_as_moderator["response"]
        assert url["url"] not in [x["url"] for x in response.json()], f"Removed URL {url} still in system"

    def test_verify_moderator_can_readd_url_removed_by_moderator(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        remove_url_as_moderator,
    ):
        """@brief Verify that moderator can readd a URL deleted by a moderator"""
        session = http_session.session("moderator")

        expected_url, response = remove_url_as_moderator["expected_url"], remove_url_as_moderator["response"]
        assert expected_url["url"] not in [
            x["url"] for x in response.json()
        ], f"Removed URL {expected_url} still in system"

        response = helpers.add_url(session, expected_url)
        assert response.ok, f"The addition of URL {expected_url} failed"

        response = helpers.get_urls(session)
        assert response.ok, "Getting the URLs failed"

        urls_in_system = response.json()

        assert expected_url["url"] in [
            x["url"] for x in urls_in_system
        ], f"The re-added URL {expected_url} is still not found in the response"

    def test_verify_moderator_can_delete_url_added_by_administrator(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        add_all_unique_urls_as_administrator,
        login_moderator,
    ):
        """@brief Verify that moderator can delete a URL added by an administrator"""

        expected_url = tst_configuration.urls["unique"][0]
        session = http_session.session("moderator")

        assert all(x.ok for x in add_all_unique_urls_as_administrator), logger.error(
            "Addition of some URLs failed: %s",
            [
                (resp.request.url, resp.request.headers, resp.request.body)
                for resp in add_all_unique_urls_as_administrator
                if not resp.ok
            ],
        )

        response = helpers.delete_url(session, expected_url["url"])
        assert response.ok, f"Deleting URL {expected_url} failed"

        response = helpers.get_urls(session)
        assert response.ok, "Getting the URLs failed"

        urls_in_system = response.json()

        assert expected_url["url"] not in [
            x["url"] for x in urls_in_system
        ], f"The removed URL {expected_url} is still found in the response"

    def test_verify_moderator_can_readd_url_removed_by_administrator(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        remove_url_as_administrator,
        login_moderator,
    ):
        """@brief Verify that moderator can readd a URL deleted by an administrator"""
        session = http_session.session("moderator")
        expected_url, response = remove_url_as_administrator["expected_url"], remove_url_as_administrator["response"]

        assert response.ok, "Removing the URL failed"
        urls_in_system = response.json()

        assert expected_url["url"] not in [
            x["url"] for x in urls_in_system
        ], f"The removed URL {expected_url} is still found in the response"

        response = helpers.add_url(session, expected_url)
        assert response.ok, f"The addition of URL {expected_url} failed"

        response = helpers.get_urls(session)
        assert response.ok, "Getting the URLs failed"

        urls_in_system = response.json()

        assert expected_url["url"] in [
            x["url"] for x in urls_in_system
        ], f"The re-added URL {expected_url} is still not found in the response"


@pytest.mark.negative
@pytest.mark.usefixtures("reset_db_data")
class TestModifyURLNegatives:
    """@brief Test modification of URLs functionality - Fully negative section

    Features
    =========
    * Deactivate URL
    * Reactivate URL
    * Re-adding de-activated not allowed

    Tests
    =====
    * [x] NEG As administrator after logout
        * [x] Add
        * [x] Remove
    * [x] NEG As reader
        * [x] Add
        * [x] Remove
    * [x] NEG As Voter
        * [x] Add
        * [x] Remove
    * [x] NEG As anonymous
        * [x] Add
        * [x] Remove
    """

    @pytest.mark.parametrize(
        "user, action, setup_action, user_login",
        [
            # Deletions
            pytest.param("voter", "delete", "add_all_unique_urls_as_administrator", "login_voter"),
            pytest.param("reader", "delete", "add_all_unique_urls_as_administrator", "login_reader"),
            pytest.param("administrator", "delete", "add_all_unique_urls_as_administrator", "logout_administrator"),
            pytest.param("anonymous", "delete", "add_all_unique_urls_as_administrator", "login_moderator"),
            # Additions
            pytest.param("administrator", "add", "remove_url_as_administrator", "logout_administrator"),
            pytest.param("voter", "add", "remove_url_as_administrator", "login_voter"),
            pytest.param("reader", "add", "remove_url_as_administrator", "login_reader"),
            pytest.param("anonymous", "add", "remove_url_as_administrator", "login_moderator"),
        ],
    )
    def test_verify_other_user_cannot_act_on_url_actioned_by_administrator(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        user,
        action,
        setup_action,
        user_login,
        request,
    ):
        """@brief Run a suite of similar tests that verify that a user can't perform the "next" action
        (delete / re-enable) following a setup by the administrator"""
        logger.info("Testing action %s by user %s", action, user)

        url_to_use = tst_configuration.urls["unique"][0]
        get_session = http_session.session(user)
        run_session = http_session.session(user)

        request.getfixturevalue(setup_action)
        request.getfixturevalue(user_login)

        # In these instances, `get` would also fail
        if user_login == "logout_administrator" or user == "anonymous":
            request.getfixturevalue("login_moderator")
            get_session = http_session.session("moderator")

        if user_login == "logout_administrator":
            request.getfixturevalue("get_admin_logouter")()

        if action == "delete":
            response = helpers.get_urls(get_session)
            assert response.ok, "Couldn't read URLs list to ensure removal won't happen"
            assert url_to_use["url"] in [x["url"] for x in response.json()], f"URL {url_to_use} not in URLs list"

            response = helpers.delete_url(run_session, url_to_use)
            assert not response.ok, f"Removal of URL by {user} succeeded when it shouldn't"

            response = helpers.get_urls(get_session)
            assert response.ok, "Couldn't read URLs list to ensure removal did not happen"
            assert url_to_use["url"] in [
                x["url"] for x in response.json()
            ], f"URL {url_to_use} was removed from the list"

        if action == "add":
            response = helpers.get_urls(get_session)
            assert response.ok, "Couldn't read URLs list to ensure removal won't happen"
            assert url_to_use["url"] not in [x["url"] for x in response.json()], f"URL {url_to_use} not in URLs list"

            response = helpers.add_url(run_session, url_to_use)
            assert not response.ok, logger.error("Addition of URL by %s succeeded when it shouldn't", user)

            response = helpers.get_urls(get_session)
            assert response.ok, "Couldn't read URLs list to ensure addition did not happen"
            assert url_to_use["url"] not in [
                x["url"] for x in response.json()
            ], f"URL {url_to_use} was removed from the list"

        # The administrator login is a class-scoped fixture and so the administrator should be logged-back in after the test finishes
        if user_login == "logout_administrator":
            http_session.close("administrator")
            request.getfixturevalue("get_admin_loginer")()

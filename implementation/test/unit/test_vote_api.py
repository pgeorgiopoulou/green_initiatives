#!/usr/bin/env python3
# pylint: disable=fixme, unused-argument, redefined-outer-name, too-many-arguments,too-many-positional-arguments
"""@file implements tests for the Vote api

NOTE: The Administrator *should* have the ability to modify multiple votes. Not examined here, assumed that they do so
by directly modifying the database
"""
import pytest


@pytest.mark.usefixtures("reset_db_data")
class TestCastVote:
    """@class Tests the case of a single vote being cast by a user on a single URL"""

    @pytest.mark.parametrize(
        "user, action, setup_action, user_login, expected_vote_count",
        [
            pytest.param("administrator", "upvote", "add_all_unique_urls_as_administrator", "login_administrator", 1),
            pytest.param("voter", "upvote", "add_all_unique_urls_as_administrator", "login_voter", 1),
            pytest.param(
                "administrator",
                "downvote",
                "add_all_unique_urls_as_administrator",
                "login_administrator",
                -1,
            ),
            pytest.param("voter", "downvote", "add_all_unique_urls_as_administrator", "login_voter", -1),
        ],
    )
    def test_verify_single_user_single_vote_succeeds(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        user,
        action,
        setup_action,
        user_login,
        expected_vote_count,
        request,
    ):
        """@brief Run a suite of similar tests that verify that a user X can upvote a single URL"""

        logger.info("Testing action %s by user %s", action, user)
        url_to_use = tst_configuration.urls["unique"][0]
        session = http_session.session(user)

        request.getfixturevalue(setup_action)
        request.getfixturevalue(user_login)

        if action == "upvote":
            response = helpers.upvote_url(session, url_to_use, logger)
        if action == "downvote":
            response = helpers.downvote_url(session, url_to_use, logger)
        assert response.ok, logger.error("%s of URL %s as user %s failed", action, url_to_use, user)

        url_votes = helpers.get_url_votes(session, url_to_use, logger)
        assert url_votes.ok, logger.error("Failed getting the votes for the URL")
        assert url_votes.json().get("totalvotes", None) == expected_vote_count, logger.error(
            "URL not shown as voted for",
        )

    @pytest.mark.negative
    @pytest.mark.parametrize(
        "user, action, setup_action, user_login, expected_vote_count",
        [
            pytest.param("moderator", "upvote", "add_all_unique_urls_as_administrator", "login_moderator", 1),
            pytest.param("reader", "upvote", "add_all_unique_urls_as_administrator", "login_reader", 1),
            pytest.param("anonymous", "upvote", "add_all_unique_urls_as_administrator", "login_reader", 1),
            pytest.param("administrator", "upvote", "add_all_unique_urls_as_administrator", "logout_administrator", 1),
            pytest.param("moderator", "downvote", "add_all_unique_urls_as_administrator", "login_moderator", 1),
            pytest.param("reader", "downvote", "add_all_unique_urls_as_administrator", "login_reader", 1),
            pytest.param("anonymous", "downvote", "add_all_unique_urls_as_administrator", "login_reader", 1),
            pytest.param(
                "administrator",
                "downvote",
                "add_all_unique_urls_as_administrator",
                "logout_administrator",
                1,
            ),
        ],
    )
    def test_verify_single_user_single_vote_fails(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        user,
        action,
        setup_action,
        user_login,
        expected_vote_count,
        request,
    ):
        """@brief Run a suite of similar tests that verify that a user X can *NOT* upvote a single URL"""

        logger.info("Testing action %s by user %s", action, user)
        url_to_use = tst_configuration.urls["unique"][0]

        session = http_session.session(user)

        request.getfixturevalue(setup_action)
        request.getfixturevalue(user_login)
        if user_login == "logout_administrator":
            request.getfixturevalue("get_admin_logouter")()
            http_session.close("administrator")

        if action == "upvote":
            response = helpers.upvote_url(session, url_to_use, logger)
        if action == "downvote":
            response = helpers.downvote_url(session, url_to_use, logger)
        assert not response.ok, logger.error("%s of URL %s as user %s succeeded", action, url_to_use, user)

        url_votes = helpers.get_url_votes(session, url_to_use, logger)
        assert not url_votes.ok, logger.error("Got votes for the URL")

        if user_login == "logout_administrator":
            http_session.close("administrator")
            request.getfixturevalue("get_admin_loginer")()

    @pytest.mark.parametrize(
        "votes, expected_vote_count",
        [
            pytest.param([{"administrator": "upvote"}, {"administrator": "upvote"}], 1),
            pytest.param([{"administrator": "upvote"}, {"voter": "upvote"}], 2),
            pytest.param([{"administrator": "upvote"}, {"administrator": "downvote"}], -1),
            pytest.param([{"administrator": "upvote"}, {"voter": "downvote"}], 0),
            pytest.param([{"voter": "upvote"}, {"administrator": "upvote"}], 2),
            pytest.param([{"voter": "upvote"}, {"voter": "upvote"}], 1),
            pytest.param([{"voter": "upvote"}, {"administrator": "downvote"}], 0),
            pytest.param([{"voter": "upvote"}, {"voter": "downvote"}], -1),
            pytest.param([{"administrator": "downvote"}, {"administrator": "upvote"}], 1),
            pytest.param([{"administrator": "downvote"}, {"voter": "upvote"}], 0),
            pytest.param([{"administrator": "downvote"}, {"administrator": "downvote"}], -1),
            pytest.param([{"administrator": "downvote"}, {"voter": "downvote"}], -2),
            pytest.param([{"voter": "downvote"}, {"administrator": "upvote"}], 0),
            pytest.param([{"voter": "downvote"}, {"voter": "upvote"}], 1),
            pytest.param([{"voter": "downvote"}, {"administrator": "downvote"}], -2),
            pytest.param([{"voter": "downvote"}, {"voter": "downvote"}], -1),
        ],
    )
    def test_verify_multiple_users_single_url_voting_works_correctly(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        votes,
        add_all_unique_urls_as_administrator,
        expected_vote_count,
        request,
    ):
        """@brief Run a suite of similar tests that verify that voting works correctly when multiple valid users vote
        the same URL"""

        logger.info("Veryfing that multiple votes can be cast correctly on single URL.")
        logger.info("Scenario: %s, expected resulting votes: %s.", votes, expected_vote_count)
        url_to_use = tst_configuration.urls["unique"][0]

        sessions = {}
        usernames = [y for x in votes for y in list(x.keys())]
        for user in set(usernames):
            request.getfixturevalue(f"login_{user}")
            sessions[user] = http_session.session(user)

        for vote in votes:
            for user, action in vote.items():
                if action == "upvote":
                    helpers.upvote_url(sessions[user], url_to_use, logger)
                elif action == "downvote":
                    helpers.downvote_url(sessions[user], url_to_use, logger)
                else:
                    raise ValueError(f"Unknown action {action}")

        request.getfixturevalue("login_administrator")
        sessions["administrator"] = http_session.session("administrator")
        url_votes = helpers.get_url_votes(sessions["administrator"], url_to_use, logger)

        assert url_votes.ok, logger.error("Failed getting the votes for the URL")
        actual_votes = url_votes.json().get("totalvotes", None)
        assert actual_votes == expected_vote_count, logger.error(
            "URL vote count %s not matching expected value %s",
            actual_votes,
            expected_vote_count,
        )

    @pytest.mark.parametrize(
        "votes",
        [
            pytest.param([(0, "upvote", "administrator", 1), (1, "upvote", "administrator", 1)]),
            pytest.param([(0, "upvote", "administrator", 1), (1, "upvote", "voter", 1)]),
            pytest.param([(0, "upvote", "administrator", 1), (1, "downvote", "administrator", -1)]),
            pytest.param([(0, "upvote", "administrator", 1), (1, "downvote", "voter", -1)]),
            pytest.param([(0, "upvote", "voter", 1), (1, "upvote", "administrator", 1)]),
            pytest.param([(0, "upvote", "voter", 1), (1, "upvote", "voter", 1)]),
            pytest.param([(0, "upvote", "voter", 1), (1, "downvote", "administrator", -1)]),
            pytest.param([(0, "upvote", "voter", 1), (1, "downvote", "voter", -1)]),
            pytest.param([(0, "downvote", "administrator", -1), (1, "upvote", "administrator", 1)]),
            pytest.param([(0, "downvote", "administrator", -1), (1, "upvote", "voter", 1)]),
            pytest.param([(0, "downvote", "administrator", -1), (1, "downvote", "administrator", -1)]),
            pytest.param([(0, "downvote", "administrator", -1), (1, "downvote", "voter", -1)]),
            pytest.param([(0, "downvote", "voter", -1), (1, "upvote", "administrator", 1)]),
            pytest.param([(0, "downvote", "voter", -1), (1, "upvote", "voter", 1)]),
            pytest.param([(0, "downvote", "voter", -1), (1, "downvote", "administrator", -1)]),
            pytest.param([(0, "downvote", "voter", -1), (1, "downvote", "voter", -1)]),
            pytest.param([(1, "upvote", "administrator", 1), (0, "upvote", "administrator", 1)]),
            pytest.param([(1, "upvote", "administrator", 1), (0, "upvote", "voter", 1)]),
            pytest.param([(1, "upvote", "administrator", 1), (0, "downvote", "administrator", -1)]),
            pytest.param([(1, "upvote", "administrator", 1), (0, "downvote", "voter", -1)]),
            pytest.param([(1, "upvote", "voter", 1), (0, "upvote", "administrator", 1)]),
            pytest.param([(1, "upvote", "voter", 1), (0, "upvote", "voter", 1)]),
            pytest.param([(1, "upvote", "voter", 1), (0, "downvote", "administrator", -1)]),
            pytest.param([(1, "upvote", "voter", 1), (0, "downvote", "voter", -1)]),
            pytest.param([(1, "downvote", "administrator", -1), (0, "upvote", "administrator", 1)]),
            pytest.param([(1, "downvote", "administrator", -1), (0, "upvote", "voter", 1)]),
            pytest.param([(1, "downvote", "administrator", -1), (0, "downvote", "administrator", -1)]),
            pytest.param([(1, "downvote", "administrator", -1), (0, "downvote", "voter", -1)]),
            pytest.param([(1, "downvote", "voter", -1), (0, "upvote", "administrator", 1)]),
            pytest.param([(1, "downvote", "voter", -1), (0, "upvote", "voter", 1)]),
            pytest.param([(1, "downvote", "voter", -1), (0, "downvote", "administrator", -1)]),
            pytest.param([(1, "downvote", "voter", -1), (0, "downvote", "voter", -1)]),
        ],
    )
    def test_verify_multiple_users_multiple_urls_voting_works_correctly(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        votes,
        add_all_unique_urls_as_administrator,
        request,
    ):
        """@brief Run a suite of similar tests that verify that voting works correctly when multiple valid users vote
        different URLs. The URLs are referenced as their index in the unique_urls structure"""

        logger.info("Veryfing that multiple users can cast votes successfully on multiple URLs.")
        logger.info("Scenario: %s", votes)

        sessions = {}
        expected_results = {}
        for vote in votes:
            url_idx, action, user, expected_result = vote
            url = tst_configuration.urls["unique"][url_idx]
            expected_results[url["url"]] = expected_result
            request.getfixturevalue(f"login_{user}")
            sessions[user] = http_session.session(user)
            if action == "upvote":
                response = helpers.upvote_url(sessions[user], url, logger)
            elif action == "downvote":
                response = helpers.downvote_url(sessions[user], url, logger)
            else:
                raise ValueError(f"Unknown action {action}")
            assert response.ok, logger.error("Couldn't %s URL %s", action, url)

        request.getfixturevalue("login_administrator")
        sessions["administrator"] = http_session.session("administrator")
        all_votes = helpers.get_all_votes(sessions["administrator"], logger)
        assert all_votes.ok, logger.error("Failed getting the votes for all URLs")
        url_votes = {x["url"]: x["totalvotes"] for x in all_votes.json()}
        for url, value in expected_results.items():
            assert url_votes[url] == value, logger.error(
                "Votes for url %s: Actual value %d doesn't match expected value %d",
                url,
                url_votes[url],
                value,
            )

    @pytest.mark.parametrize(
        "votes",
        [
            pytest.param(
                [
                    (3, "reader", "upvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (3, "logged-out administrator", "upvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                    (1, "administrator", "downvote", True, -1),
                ],
                id=(
                    "reader upvotes unique_url_3, reader downvotes unique_url_0,"
                    " administrator downvotes unique_url_3, logged-out administrator upvotes unique_url_3,"
                    " administrator downvotes unique_url_0, administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "moderator", "downvote", False, 0),
                    (1, "administrator", "upvote", True, 1),
                    (0, "anonymous", "downvote", False, 0),
                    (0, "moderator", "downvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (3, "moderator", "upvote", False, 0),
                ],
                id=(
                    "moderator downvotes unique_url_1, administrator upvotes unique_url_1,"
                    " anonymous downvotes unique_url_0, moderator downvotes unique_url_0,"
                    " voter upvotes unique_url_3, moderator upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "administrator", "upvote", True, 1),
                    (0, "administrator", "downvote", True, -1),
                    (0, "moderator", "downvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (0, "administrator", "upvote", True, 1),
                    (0, "moderator", "upvote", False, 0),
                ],
                id=(
                    "administrator upvotes unique_url_1, administrator downvotes unique_url_0,"
                    " moderator downvotes unique_url_0, administrator downvotes unique_url_3,"
                    " administrator upvotes unique_url_0, moderator upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "downvote", False, 0),
                    (0, "reader", "upvote", False, 0),
                    (0, "voter", "upvote", True, 1),
                    (1, "moderator", "upvote", False, 0),
                    (1, "voter", "upvote", True, 1),
                    (3, "logged-out administrator", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_0, reader upvotes unique_url_0,"
                    " voter upvotes unique_url_0, moderator upvotes unique_url_1, voter upvotes unique_url_1,"
                    " logged-out administrator upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "administrator", "upvote", True, 1),
                    (0, "moderator", "downvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                    (3, "moderator", "downvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (1, "administrator", "downvote", True, -1),
                ],
                id=(
                    "administrator upvotes unique_url_1, moderator downvotes unique_url_0,"
                    " administrator downvotes unique_url_0, moderator downvotes unique_url_3,"
                    " administrator downvotes unique_url_3, administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "reader", "upvote", False, 0),
                    (0, "anonymous", "upvote", False, 0),
                    (3, "logged-out administrator", "downvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                    (1, "logged-out administrator", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                ],
                id=(
                    "reader upvotes unique_url_1, anonymous upvotes unique_url_0,"
                    " logged-out administrator downvotes unique_url_3, voter downvotes unique_url_3,"
                    " logged-out administrator upvotes unique_url_1, anonymous upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "reader", "downvote", False, 0),
                    (1, "logged-out administrator", "downvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (0, "logged-out administrator", "downvote", False, 0),
                    (0, "voter", "downvote", True, -1),
                ],
                id=(
                    "reader downvotes unique_url_1, logged-out administrator downvotes unique_url_1,"
                    " reader downvotes unique_url_3, anonymous downvotes unique_url_3,"
                    " logged-out administrator downvotes unique_url_0, voter downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "administrator", "upvote", True, 1),
                    (1, "voter", "upvote", True, 1),
                    (3, "moderator", "downvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (1, "administrator", "downvote", True, 0),
                    (1, "voter", "upvote", True, 0),
                ],
                id=(
                    "administrator upvotes unique_url_0, voter upvotes unique_url_1,"
                    " moderator downvotes unique_url_3, logged-out administrator upvotes unique_url_0,"
                    " administrator downvotes unique_url_1, voter upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "downvote", True, -1),
                    (1, "moderator", "downvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (1, "voter", "downvote", True, -2),
                    (0, "administrator", "downvote", True, -2),
                    (1, "reader", "downvote", False, 0),
                ],
                id=(
                    "voter downvotes unique_url_0, moderator downvotes unique_url_1,"
                    " administrator downvotes unique_url_1, voter downvotes unique_url_1,"
                    " administrator downvotes unique_url_0, reader downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "reader", "downvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                    (1, "voter", "upvote", True, 1),
                    (1, "voter", "downvote", True, -1),
                    (1, "voter", "downvote", True, -1),
                ],
                id=(
                    "reader downvotes unique_url_0, logged-out administrator upvotes unique_url_0,"
                    " reader downvotes unique_url_1, voter upvotes unique_url_1, voter downvotes unique_url_1,"
                    " voter downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "anonymous", "downvote", False, 0),
                    (1, "moderator", "upvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                    (3, "moderator", "upvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                    (1, "logged-out administrator", "downvote", False, 0),
                ],
                id=(
                    "anonymous downvotes unique_url_0, moderator upvotes unique_url_1,"
                    " voter downvotes unique_url_3, moderator upvotes unique_url_3,"
                    " reader downvotes unique_url_1, logged-out administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "upvote", False, 0),
                    (1, "moderator", "downvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                    (0, "logged-out administrator", "downvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                    (0, "voter", "upvote", True, 1),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_0, moderator downvotes unique_url_1,"
                    " anonymous downvotes unique_url_0, logged-out administrator downvotes unique_url_0,"
                    " reader downvotes unique_url_1, voter upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "anonymous", "upvote", False, 0),
                    (0, "voter", "downvote", True, -1),
                    (0, "reader", "downvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (0, "voter", "downvote", True, -1),
                ],
                id=(
                    "anonymous upvotes unique_url_0, voter downvotes unique_url_0,"
                    " reader downvotes unique_url_0, reader downvotes unique_url_0,"
                    " anonymous upvotes unique_url_3, voter downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "upvote", False, 0),
                    (1, "anonymous", "downvote", False, 0),
                    (3, "logged-out administrator", "downvote", False, 0),
                    (1, "moderator", "upvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                    (3, "reader", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_0, anonymous downvotes unique_url_1,"
                    " logged-out administrator downvotes unique_url_3, moderator upvotes unique_url_1,"
                    " voter downvotes unique_url_3, reader upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "upvote", True, 1),
                    (3, "reader", "downvote", False, 0),
                    (1, "anonymous", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (0, "voter", "upvote", True, 1),
                    (0, "voter", "downvote", True, -1),
                ],
                id=(
                    "voter upvotes unique_url_0, reader downvotes unique_url_3, anonymous upvotes unique_url_1,"
                    " anonymous upvotes unique_url_3, voter upvotes unique_url_0,"
                    " voter downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (3, "logged-out administrator", "upvote", False, 0),
                    (1, "anonymous", "upvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                    (0, "reader", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (1, "anonymous", "downvote", False, 0),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_3, anonymous upvotes unique_url_1,"
                    " anonymous downvotes unique_url_0, reader upvotes unique_url_0,"
                    " anonymous upvotes unique_url_3, anonymous downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "reader", "downvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (0, "anonymous", "upvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (3, "administrator", "upvote", True, 1),
                    (1, "logged-out administrator", "downvote", False, 0),
                ],
                id=(
                    "reader downvotes unique_url_1, anonymous upvotes unique_url_3,"
                    " anonymous upvotes unique_url_0, administrator downvotes unique_url_3,"
                    " administrator upvotes unique_url_3, logged-out administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "anonymous", "upvote", False, 0),
                    (1, "anonymous", "upvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (0, "administrator", "upvote", True, 1),
                    (0, "administrator", "upvote", True, 1),
                    (1, "reader", "downvote", False, 0),
                ],
                id=(
                    "anonymous upvotes unique_url_0, anonymous upvotes unique_url_1,"
                    " voter upvotes unique_url_3, administrator upvotes unique_url_0,"
                    " administrator upvotes unique_url_0, reader downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "upvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                    (0, "logged-out administrator", "downvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (1, "voter", "upvote", True, 1),
                    (3, "reader", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_0, administrator upvotes unique_url_3,"
                    " logged-out administrator downvotes unique_url_0, anonymous downvotes unique_url_3,"
                    " voter upvotes unique_url_1, reader upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "moderator", "downvote", False, 0),
                    (3, "moderator", "upvote", False, 0),
                    (0, "moderator", "downvote", False, 0),
                    (1, "anonymous", "upvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                    (1, "moderator", "upvote", False, 0),
                ],
                id=(
                    "moderator downvotes unique_url_1, moderator upvotes unique_url_3,"
                    " moderator downvotes unique_url_0, anonymous upvotes unique_url_1,"
                    " reader downvotes unique_url_1, moderator upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "administrator", "downvote", True, -1),
                    (3, "voter", "downvote", True, -1),
                    (1, "logged-out administrator", "downvote", False, 0),
                    (0, "reader", "upvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (3, "reader", "upvote", False, 0),
                ],
                id=(
                    "administrator downvotes unique_url_0, voter downvotes unique_url_3,"
                    " logged-out administrator downvotes unique_url_1, reader upvotes unique_url_0,"
                    " reader downvotes unique_url_0, reader upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "logged-out administrator", "downvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (0, "reader", "upvote", False, 0),
                    (0, "voter", "upvote", True, 1),
                    (3, "logged-out administrator", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_1, reader downvotes unique_url_3,"
                    " reader upvotes unique_url_0, voter upvotes unique_url_0,"
                    " logged-out administrator upvotes unique_url_3, anonymous upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "moderator", "downvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                    (3, "anonymous", "upvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (3, "administrator", "upvote", True, 2),
                ],
                id=(
                    "moderator downvotes unique_url_0, administrator downvotes unique_url_0,"
                    " anonymous upvotes unique_url_3, reader downvotes unique_url_0,"
                    " voter upvotes unique_url_3, administrator upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "reader", "downvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                    (1, "reader", "upvote", False, 0),
                ],
                id=(
                    "reader downvotes unique_url_0, administrator upvotes unique_url_3,"
                    " logged-out administrator upvotes unique_url_0, anonymous downvotes unique_url_3,"
                    " anonymous downvotes unique_url_0, reader upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "logged-out administrator", "upvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (0, "administrator", "upvote", True, 1),
                    (1, "anonymous", "downvote", False, 0),
                    (1, "voter", "upvote", True, 0),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_1, reader downvotes unique_url_0,"
                    " administrator downvotes unique_url_1, administrator upvotes unique_url_0,"
                    " anonymous downvotes unique_url_1, voter upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (0, "anonymous", "downvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                    (0, "moderator", "downvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (3, "anonymous", "downvote", False, 0),
                    (3, "voter", "upvote", True, 2),
                ],
                id=(
                    "anonymous downvotes unique_url_0, administrator upvotes unique_url_3,"
                    " moderator downvotes unique_url_0, administrator downvotes unique_url_1,"
                    " anonymous downvotes unique_url_3, voter upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "anonymous", "upvote", False, 0),
                    (0, "administrator", "upvote", True, 1),
                    (1, "reader", "upvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (0, "anonymous", "upvote", False, 0),
                ],
                id=(
                    "anonymous upvotes unique_url_0, administrator upvotes unique_url_0,"
                    " reader upvotes unique_url_1, reader downvotes unique_url_1, voter upvotes unique_url_3,"
                    " anonymous upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (3, "reader", "upvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                    (1, "anonymous", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (1, "moderator", "downvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                ],
                id=(
                    "reader upvotes unique_url_3, administrator downvotes unique_url_0,"
                    " anonymous upvotes unique_url_1, anonymous upvotes unique_url_3,"
                    " moderator downvotes unique_url_1, voter downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (3, "moderator", "downvote", False, 0),
                    (1, "anonymous", "downvote", False, 0),
                    (0, "anonymous", "upvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (3, "logged-out administrator", "upvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                ],
                id=(
                    "moderator downvotes unique_url_3, anonymous downvotes unique_url_1,"
                    " anonymous upvotes unique_url_0, administrator downvotes unique_url_1,"
                    " logged-out administrator upvotes unique_url_3, administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "anonymous", "downvote", False, 0),
                    (1, "moderator", "upvote", False, 0),
                    (3, "logged-out administrator", "downvote", False, 0),
                    (0, "logged-out administrator", "downvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (0, "voter", "upvote", True, 1),
                ],
                id=(
                    "anonymous downvotes unique_url_1, moderator upvotes unique_url_1,"
                    " logged-out administrator downvotes unique_url_3, logged-out administrator downvotes unique_url_0,"
                    " reader downvotes unique_url_3, voter upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "downvote", False, 0),
                    (0, "administrator", "upvote", True, 1),
                    (1, "anonymous", "downvote", False, 0),
                    (1, "anonymous", "downvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_0, administrator upvotes unique_url_0,"
                    " anonymous downvotes unique_url_1, anonymous downvotes unique_url_1,"
                    " logged-out administrator upvotes unique_url_0, administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "reader", "upvote", False, 0),
                    (3, "logged-out administrator", "upvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (1, "moderator", "downvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                    (0, "administrator", "upvote", True, 1),
                ],
                id=(
                    "reader upvotes unique_url_1, logged-out administrator upvotes unique_url_3,"
                    " administrator downvotes unique_url_3, moderator downvotes unique_url_1,"
                    " reader downvotes unique_url_1, administrator upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (3, "voter", "upvote", True, 1),
                    (1, "moderator", "downvote", False, 0),
                    (3, "moderator", "upvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (1, "logged-out administrator", "upvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                ],
                id=(
                    "voter upvotes unique_url_3, moderator downvotes unique_url_1,"
                    " moderator upvotes unique_url_3, anonymous downvotes unique_url_3,"
                    " logged-out administrator upvotes unique_url_1, administrator downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "downvote", True, -1),
                    (1, "logged-out administrator", "upvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                    (1, "moderator", "upvote", False, 0),
                    (3, "administrator", "upvote", True, 0),
                    (0, "administrator", "downvote", True, -2),
                ],
                id=(
                    "voter downvotes unique_url_0, logged-out administrator upvotes unique_url_1,"
                    " voter downvotes unique_url_3, moderator upvotes unique_url_1,"
                    " administrator upvotes unique_url_3, administrator downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "upvote", False, 0),
                    (3, "reader", "upvote", False, 0),
                    (0, "moderator", "upvote", False, 0),
                    (3, "moderator", "downvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (0, "voter", "upvote", True, 1),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_0, reader upvotes unique_url_3,"
                    " moderator upvotes unique_url_0, moderator downvotes unique_url_3,"
                    " voter upvotes unique_url_3, voter upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (3, "logged-out administrator", "downvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (3, "logged-out administrator", "downvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_3, anonymous upvotes unique_url_3,"
                    " anonymous downvotes unique_url_3, logged-out administrator downvotes unique_url_3,"
                    " anonymous downvotes unique_url_0, administrator upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (3, "moderator", "upvote", False, 0),
                    (3, "moderator", "downvote", False, 0),
                    (3, "moderator", "upvote", False, 0),
                    (3, "moderator", "downvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                    (1, "logged-out administrator", "downvote", False, 0),
                ],
                id=(
                    "moderator upvotes unique_url_3, moderator downvotes unique_url_3,"
                    " moderator upvotes unique_url_3, moderator downvotes unique_url_3,"
                    " administrator downvotes unique_url_0, logged-out administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (3, "administrator", "upvote", True, 1),
                    (1, "moderator", "downvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (0, "administrator", "upvote", True, 1),
                    (0, "anonymous", "upvote", False, 0),
                ],
                id=(
                    "administrator upvotes unique_url_3, moderator downvotes unique_url_1,"
                    " anonymous downvotes unique_url_3, anonymous downvotes unique_url_3,"
                    " administrator upvotes unique_url_0, anonymous upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (1, "administrator", "downvote", True, -1),
                    (1, "administrator", "downvote", True, -1),
                    (3, "voter", "downvote", True, -1),
                    (0, "administrator", "downvote", True, -1),
                    (3, "administrator", "upvote", True, 0),
                    (1, "voter", "downvote", True, -2),
                ],
                id=(
                    "administrator downvotes unique_url_1, administrator downvotes unique_url_1,"
                    " voter downvotes unique_url_3, administrator downvotes unique_url_0,"
                    " administrator upvotes unique_url_3, voter downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (3, "moderator", "upvote", False, 0),
                    (0, "moderator", "upvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                    (1, "anonymous", "upvote", False, 0),
                    (3, "logged-out administrator", "downvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                ],
                id=(
                    "moderator upvotes unique_url_3, moderator upvotes unique_url_0,"
                    " administrator downvotes unique_url_0, anonymous upvotes unique_url_1,"
                    " logged-out administrator downvotes unique_url_3, anonymous downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (3, "logged-out administrator", "downvote", False, 0),
                    (1, "voter", "upvote", True, 1),
                    (3, "administrator", "upvote", True, 1),
                    (3, "anonymous", "downvote", False, 0),
                    (1, "reader", "upvote", False, 0),
                    (1, "voter", "downvote", True, -1),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_3, voter upvotes unique_url_1,"
                    " administrator upvotes unique_url_3, anonymous downvotes unique_url_3,"
                    " reader upvotes unique_url_1, voter downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "moderator", "downvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (3, "anonymous", "upvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                ],
                id=(
                    "moderator downvotes unique_url_1, anonymous upvotes unique_url_3,"
                    " anonymous upvotes unique_url_3, anonymous upvotes unique_url_3,"
                    " logged-out administrator upvotes unique_url_0, voter downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "downvote", True, -1),
                    (1, "reader", "downvote", False, 0),
                    (0, "moderator", "upvote", False, 0),
                    (0, "voter", "downvote", True, -1),
                    (3, "administrator", "upvote", True, 1),
                    (3, "voter", "downvote", True, 0),
                ],
                id=(
                    "voter downvotes unique_url_0, reader downvotes unique_url_1,"
                    " moderator upvotes unique_url_0, voter downvotes unique_url_0,"
                    " administrator upvotes unique_url_3, voter downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (3, "reader", "upvote", False, 0),
                    (1, "moderator", "downvote", False, 0),
                    (0, "logged-out administrator", "downvote", False, 0),
                    (3, "reader", "upvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                ],
                id=(
                    "reader upvotes unique_url_3, moderator downvotes unique_url_1,"
                    " logged-out administrator downvotes unique_url_0, reader upvotes unique_url_3,"
                    " reader downvotes unique_url_3, voter downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (3, "anonymous", "downvote", False, 0),
                    (1, "anonymous", "upvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                    (1, "anonymous", "upvote", False, 0),
                    (0, "reader", "upvote", False, 0),
                    (1, "logged-out administrator", "downvote", False, 0),
                ],
                id=(
                    "anonymous downvotes unique_url_3, anonymous upvotes unique_url_1,"
                    " voter downvotes unique_url_3, anonymous upvotes unique_url_1,"
                    " reader upvotes unique_url_0, logged-out administrator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (3, "logged-out administrator", "downvote", False, 0),
                    (3, "moderator", "downvote", False, 0),
                    (3, "voter", "downvote", True, -1),
                    (0, "anonymous", "upvote", False, 0),
                    (1, "logged-out administrator", "downvote", False, 0),
                    (3, "logged-out administrator", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_3, moderator downvotes unique_url_3,"
                    " voter downvotes unique_url_3, anonymous upvotes unique_url_0,"
                    " logged-out administrator downvotes unique_url_1, logged-out administrator upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "moderator", "downvote", False, 0),
                    (0, "moderator", "upvote", False, 0),
                    (0, "reader", "upvote", False, 0),
                    (0, "administrator", "upvote", True, 1),
                    (0, "moderator", "downvote", False, 0),
                    (0, "logged-out administrator", "downvote", False, 0),
                ],
                id=(
                    "moderator downvotes unique_url_1, moderator upvotes unique_url_0,"
                    " reader upvotes unique_url_0, administrator upvotes unique_url_0,"
                    " moderator downvotes unique_url_0, logged-out administrator downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "downvote", True, -1),
                    (3, "reader", "upvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (0, "administrator", "downvote", True, -2),
                    (0, "administrator", "downvote", True, -2),
                ],
                id=(
                    "voter downvotes unique_url_0, reader upvotes unique_url_3,"
                    " anonymous downvotes unique_url_3, reader downvotes unique_url_3,"
                    " administrator downvotes unique_url_0, administrator downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "reader", "downvote", False, 0),
                    (1, "logged-out administrator", "downvote", False, 0),
                    (3, "moderator", "downvote", False, 0),
                    (0, "anonymous", "upvote", False, 0),
                    (0, "administrator", "upvote", True, 1),
                    (0, "logged-out administrator", "upvote", False, 0),
                ],
                id=(
                    "reader downvotes unique_url_0, logged-out administrator downvotes unique_url_1,"
                    " moderator downvotes unique_url_3, anonymous upvotes unique_url_0,"
                    " administrator upvotes unique_url_0, logged-out administrator upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "reader", "upvote", False, 0),
                    (1, "voter", "downvote", True, -1),
                    (3, "moderator", "downvote", False, 0),
                    (1, "voter", "upvote", True, 1),
                    (0, "voter", "upvote", True, 1),
                    (0, "anonymous", "upvote", False, 0),
                ],
                id=(
                    "reader upvotes unique_url_0, voter downvotes unique_url_1,"
                    " moderator downvotes unique_url_3, voter upvotes unique_url_1, voter upvotes unique_url_0,"
                    " anonymous upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (3, "moderator", "upvote", False, 0),
                    (0, "moderator", "downvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                    (3, "anonymous", "upvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (3, "voter", "downvote", True, 0),
                ],
                id=(
                    "moderator upvotes unique_url_3, moderator downvotes unique_url_0,"
                    " administrator upvotes unique_url_3, anonymous upvotes unique_url_3,"
                    " administrator downvotes unique_url_1, voter downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "logged-out administrator", "downvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (0, "moderator", "upvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                    (3, "moderator", "upvote", False, 0),
                    (0, "administrator", "downvote", True, -1),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_0, logged-out administrator upvotes unique_url_0,"
                    " moderator upvotes unique_url_0, administrator upvotes unique_url_3,"
                    " moderator upvotes unique_url_3, administrator downvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (0, "administrator", "downvote", True, -1),
                    (3, "anonymous", "downvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (0, "voter", "upvote", True, 0),
                    (3, "reader", "upvote", False, 0),
                    (1, "administrator", "upvote", True, 1),
                ],
                id=(
                    "administrator downvotes unique_url_0, anonymous downvotes unique_url_3,"
                    " administrator downvotes unique_url_3, voter upvotes unique_url_0,"
                    " reader upvotes unique_url_3, administrator upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "anonymous", "upvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (3, "reader", "upvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (3, "administrator", "downvote", True, 0),
                ],
                id=(
                    "anonymous upvotes unique_url_1, administrator downvotes unique_url_1,"
                    " reader upvotes unique_url_3, reader downvotes unique_url_3, voter upvotes unique_url_3,"
                    " administrator downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "voter", "upvote", True, 1),
                    (0, "logged-out administrator", "downvote", False, 0),
                    (0, "voter", "upvote", True, 1),
                    (3, "logged-out administrator", "upvote", False, 0),
                    (1, "voter", "upvote", True, 1),
                    (3, "moderator", "downvote", False, 0),
                ],
                id=(
                    "voter upvotes unique_url_1, logged-out administrator downvotes unique_url_0,"
                    " voter upvotes unique_url_0, logged-out administrator upvotes unique_url_3,"
                    " voter upvotes unique_url_1, moderator downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "downvote", True, -1),
                    (0, "administrator", "downvote", True, -2),
                    (1, "anonymous", "upvote", False, 0),
                    (1, "moderator", "upvote", False, 0),
                    (0, "anonymous", "upvote", False, 0),
                    (0, "anonymous", "upvote", False, 0),
                ],
                id=(
                    "voter downvotes unique_url_0, administrator downvotes unique_url_0,"
                    " anonymous upvotes unique_url_1, moderator upvotes unique_url_1,"
                    " anonymous upvotes unique_url_0, anonymous upvotes unique_url_0"
                ),
            ),
            pytest.param(
                [
                    (1, "administrator", "downvote", True, -1),
                    (3, "reader", "upvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (0, "voter", "downvote", True, -1),
                    (1, "logged-out administrator", "upvote", False, 0),
                ],
                id=(
                    "administrator downvotes unique_url_1, reader upvotes unique_url_3,"
                    " anonymous downvotes unique_url_0, administrator downvotes unique_url_1,"
                    " voter downvotes unique_url_0, logged-out administrator upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "voter", "downvote", True, -1),
                    (1, "moderator", "upvote", False, 0),
                    (3, "logged-out administrator", "downvote", False, 0),
                    (3, "reader", "downvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (1, "reader", "downvote", False, 0),
                ],
                id=(
                    "voter downvotes unique_url_1, moderator upvotes unique_url_1,"
                    " logged-out administrator downvotes unique_url_3, reader downvotes unique_url_3,"
                    " reader downvotes unique_url_0, reader downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (3, "voter", "downvote", True, -1),
                    (3, "voter", "upvote", True, 1),
                    (1, "voter", "downvote", True, -1),
                    (3, "moderator", "downvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (3, "moderator", "downvote", False, 0),
                ],
                id=(
                    "voter downvotes unique_url_3, voter upvotes unique_url_3, voter downvotes unique_url_1,"
                    " moderator downvotes unique_url_3, logged-out administrator upvotes unique_url_0,"
                    " moderator downvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (1, "reader", "upvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (0, "reader", "downvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                    (3, "administrator", "upvote", True, 1),
                    (1, "voter", "downvote", True, -1),
                ],
                id=(
                    "reader upvotes unique_url_1, reader downvotes unique_url_0, reader downvotes unique_url_0,"
                    " anonymous downvotes unique_url_0, administrator upvotes unique_url_3,"
                    " voter downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (3, "logged-out administrator", "downvote", False, 0),
                    (1, "moderator", "upvote", False, 0),
                    (1, "administrator", "downvote", True, -1),
                    (0, "anonymous", "downvote", False, 0),
                    (3, "administrator", "downvote", True, -1),
                    (1, "logged-out administrator", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator downvotes unique_url_3, moderator upvotes unique_url_1,"
                    " administrator downvotes unique_url_1, anonymous downvotes unique_url_0,"
                    " administrator downvotes unique_url_3, logged-out administrator upvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (3, "logged-out administrator", "upvote", False, 0),
                    (3, "voter", "upvote", True, 1),
                    (1, "logged-out administrator", "downvote", False, 0),
                    (3, "anonymous", "downvote", False, 0),
                    (0, "logged-out administrator", "upvote", False, 0),
                    (1, "moderator", "downvote", False, 0),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_3, voter upvotes unique_url_3,"
                    " logged-out administrator downvotes unique_url_1, anonymous downvotes unique_url_3,"
                    " logged-out administrator upvotes unique_url_0, moderator downvotes unique_url_1"
                ),
            ),
            pytest.param(
                [
                    (1, "logged-out administrator", "upvote", False, 0),
                    (0, "moderator", "downvote", False, 0),
                    (1, "logged-out administrator", "downvote", False, 0),
                    (0, "voter", "downvote", True, -1),
                    (0, "administrator", "upvote", True, 0),
                    (3, "moderator", "upvote", False, 0),
                ],
                id=(
                    "logged-out administrator upvotes unique_url_1, moderator downvotes unique_url_0,"
                    " logged-out administrator downvotes unique_url_1, voter downvotes unique_url_0,"
                    " administrator upvotes unique_url_0, moderator upvotes unique_url_3"
                ),
            ),
            pytest.param(
                [
                    (0, "voter", "downvote", True, -1),
                    (3, "anonymous", "downvote", False, 0),
                    (1, "voter", "downvote", True, -1),
                    (0, "reader", "downvote", False, 0),
                    (3, "logged-out administrator", "upvote", False, 0),
                    (0, "anonymous", "downvote", False, 0),
                ],
                id=(
                    "voter downvotes unique_url_0, anonymous downvotes unique_url_3,"
                    " voter downvotes unique_url_1, reader downvotes unique_url_0,"
                    " logged-out administrator upvotes unique_url_3, anonymous downvotes unique_url_0"
                ),
            ),
        ],
    )
    def test_verify_multiple_users_multiple_urls_valid_and_invalid_works_correctly(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        votes,
        add_all_unique_urls_as_administrator,
        request,
    ):
        """@brief Validate that running a mix valid and invalid voters / urls work correctly"""
        vote_functions = {"upvote": helpers.upvote_url, "downvote": helpers.downvote_url}
        expected_votes = {}
        for step in votes:
            url_idx, user, vote, valid, resulting_votes = step
            url = tst_configuration.urls["unique"][url_idx]

            # Logging administrator out or in appropriately
            if user == "administrator":
                request.getfixturevalue("get_admin_loginer")()
            elif user == "logged-out administrator":
                request.getfixturevalue("get_admin_logouter")()
            elif user == "anonymous":
                pass
            else:
                request.getfixturevalue(f"login_{user}")
            session = http_session.session(user)

            response = vote_functions[vote](session, url, logger)

            assert response.ok == valid, logger.error(
                "URL %s by %s had status %s, when expected status was %s",
                url,
                user,
                response.ok,
                valid,
            )

            if valid:
                expected_votes[url["url"]] = resulting_votes

        request.getfixturevalue("get_admin_loginer")()
        session = http_session.session("administrator")
        response = helpers.get_all_votes(session, logger)

        # Catch the "no valid votes cast in this test" scenario
        if not expected_votes:
            assert not [x for x in response.json() if x["totalvotes"] != 0], logger.error(
                "Some votes returned when none should be available: %s",
                response.text,
            )
            return

        assert response.ok, logger.error("Failed getting all votes")

        all_votes = {x["url"]: x["totalvotes"] for x in response.json()}

        votes_intersection = set(all_votes.items()).intersection(expected_votes.items())
        votes_difference = set(all_votes.items()).difference(expected_votes.items())

        assert votes_intersection == set(expected_votes.items()), logger.error(
            "Expected votes not the same as listed votes:\nexpected: %s\nlisted  :%s",
            expected_votes,
            all_votes,
        )
        assert not [x for x in votes_difference if x[1] != 0], logger.error(
            "Non-zero votes not accounted-for in expected results: %s",
            votes_difference,
        )

    def test_vote_reactivated_url_with_different_user_succeeds(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_administrator,
        login_voter,
        add_all_unique_urls_as_administrator,
        request,
    ):
        """@brief validate that a URL cannot be voted-for when deleted (inactive) but can be voted-for when
        re-activated and the votes that were cast are preserved"""

        voter_session = http_session.session("voter")
        administator_session = http_session.session("administrator")

        url_to_use = tst_configuration.urls["unique"][0]
        response = helpers.upvote_url(voter_session, url_to_use, logger)
        assert response.ok, logger.error("Failed upvoting URL as voter")

        url_votes = helpers.get_url_votes(voter_session, url_to_use, logger)
        votecount = url_votes.json().get("totalvotes", None)
        assert votecount == 1, logger.error(
            "Vote count of %s did not match expected vote count of %s",
            votecount,
            1,
        )

        response = helpers.delete_url(administator_session, url_to_use["url"])
        assert response.ok, logger.error("Failed removing URL as administrator")

        response = helpers.get_url_votes(voter_session, url_to_use, logger)
        assert not response.ok, logger.error("Got votes for deleted URL: %s", response.text)

        response = helpers.add_url(administator_session, url_to_use)
        assert response.ok, logger.error("Failed re-adding URL as administrator")

        response = helpers.upvote_url(administator_session, url_to_use, logger)
        assert response.ok, logger.error("Failed upvoting URL as voter")

        response = helpers.get_url_votes(voter_session, url_to_use, logger)
        assert response.ok, logger.error("Couldn't get votes for re-added URL: %s", response.text)

        votecount = response.json().get("totalvotes", None)
        assert votecount == 2, logger.error(
            "Vote count of %s did not match expected vote count of %s",
            votecount,
            2,
        )

    @pytest.mark.negative
    def test_revote_reactivated_url_with_different_user_succeeds(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_administrator,
        add_all_unique_urls_as_administrator,
        request,
    ):
        """@brief validate that a URL cannot be voted-for when deleted (inactive) but can be voted-for when
        re-activated and the votes that were cast are preserved, making the orinal user unable to revote"""

        administator_session = http_session.session("administrator")

        url_to_use = tst_configuration.urls["unique"][0]
        response = helpers.upvote_url(administator_session, url_to_use, logger)
        assert response.ok, logger.error("Failed upvoting URL as administator")

        url_votes = helpers.get_url_votes(administator_session, url_to_use, logger)
        votecount = url_votes.json().get("totalvotes", None)
        assert votecount == 1, logger.error(
            "Vote count of %s did not match expected vote count of %s",
            votecount,
            1,
        )

        response = helpers.delete_url(administator_session, url_to_use["url"])
        assert response.ok, logger.error("Failed removing URL as administrator")

        response = helpers.get_url_votes(administator_session, url_to_use, logger)
        assert not response.ok, logger.error("Got votes for deleted URL: %s", response.text)

        response = helpers.add_url(administator_session, url_to_use)
        assert response.ok, logger.error("Failed re-adding URL as administrator")

        response = helpers.upvote_url(administator_session, url_to_use, logger)
        assert response.ok, logger.error("Failed upvoting URL as voter")

        response = helpers.get_url_votes(administator_session, url_to_use, logger)
        assert response.ok, logger.error("Couldn't get votes for re-added URL: %s", response.text)

        votecount = response.json().get("totalvotes", None)
        assert votecount == 1, logger.error(
            "Vote count of %s did not match expected vote count of %s",
            votecount,
            1,
        )

    @pytest.mark.negative
    def test_verify_absent_url_cant_be_voted(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_administrator,
        add_all_unique_urls_as_administrator,
        request,
    ):
        """@brief Validate that a URL that's not added, can't be voted for"""

        administator_session = http_session.session("administrator")

        url_to_use = tst_configuration.urls["absent"][0]
        response = helpers.upvote_url(administator_session, url_to_use, logger)
        assert not response.ok, logger.error("Missing URL upvoted successfully")

        url_votes = helpers.get_url_votes(administator_session, url_to_use, logger)
        assert not url_votes.ok, logger.error("Got votes for URL successfully")

    @pytest.mark.negative
    def test_getting_all_votes_doesnt_include_deleted_url(
        self,
        logger,
        helpers,
        tst_configuration,
        http_session,
        login_administrator,
        add_all_unique_urls_as_administrator,
        request,
    ):
        """@brief Validate that a URL, after deletion, isn't included in "all votes" getter output"""

        administator_session = http_session.session("administrator")

        url1 = tst_configuration.urls["unique"][0]
        url2 = tst_configuration.urls["unique"][1]

        # Upvote url1 and verify
        response = helpers.upvote_url(administator_session, url1, logger)
        assert response.ok, logger.error("Failed upvoting URL %s as administator", url1)
        url_votes = helpers.get_url_votes(administator_session, url1, logger)
        votecount = url_votes.json().get("totalvotes", None)
        assert votecount == 1, logger.error(
            "Vote count of %s did not match expected vote count of %s",
            votecount,
            1,
        )

        response = helpers.upvote_url(administator_session, url2, logger)
        assert response.ok, logger.error("Failed upvoting URL %s as administator", url2)
        url_votes = helpers.get_url_votes(administator_session, url2, logger)
        votecount = url_votes.json().get("totalvotes", None)
        assert votecount == 1, logger.error(
            "Vote count of %s did not match expected vote count of %s",
            votecount,
            1,
        )

        # Upvote url2 and verify
        response = helpers.delete_url(administator_session, url1["url"])
        assert response.ok, logger.error("Failed removing URL as administrator")

        # Get all votes and verify absence
        all_votes = helpers.get_all_votes(administator_session, logger)
        assert all_votes.ok, logger.error("Failed getting the votes for all URLs")
        url_votes = {x["url"]: x["totalvotes"] for x in all_votes.json()}
        assert url2["url"] in url_votes, logger.error("Couldn't find URL %s in all votes", url2)
        assert not url1["url"] in url_votes, logger.error("Found deleted URL %s in all votes", url1)

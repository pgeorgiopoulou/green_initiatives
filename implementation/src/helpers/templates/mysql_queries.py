#!/usr/bin/env python3
"""@file MySQL query templates and strings to use"""
# pylint: disable=consider-using-f-string
import sys

from . import gi_types as mytypes

mysql_queries = {
    "create_database": "CREATE DATABASE IF NOT EXISTS {database_name};",
    "create_tables": [
        """USE {database_name};""",
        """CREATE TABLE IF NOT EXISTS roles(
        uid INT NOT NULL PRIMARY KEY,
        name VARCHAR(60) NOT NULL UNIQUE
    );""",
        """CREATE TABLE IF NOT EXISTS users(
        username VARCHAR(60) NOT NULL PRIMARY KEY,
        password VARCHAR(256) NOT NULL,
        type INT NOT NULL,
        CONSTRAINT `fk_type` FOREIGN KEY (type) REFERENCES roles (uid) ON DELETE CASCADE
    );""",
        """CREATE TABLE IF NOT EXISTS urls (
        uid VARCHAR(8) NOT NULL UNIQUE DEFAULT LEFT(MD5(RAND()), 8),
        url VARCHAR(500) NOT NULL PRIMARY KEY,
        title VARCHAR(255),
        referrer VARCHAR(60),
        inactive BOOL DEFAULT 0,
        FOREIGN KEY (referrer) REFERENCES users(username)
    );""",
        """CREATE TABLE IF NOT EXISTS votes(
        url VARCHAR(500) NOT NULL,
        voter VARCHAR(60) NOT NULL,
        vote INT NOT NULL,
        FOREIGN KEY (url) references urls(url),
        FOREIGN KEY (voter) references users(username),
        CONSTRAINT `PK_urlvoter` PRIMARY KEY(url,voter),
        CONSTRAINT CHK_Vote CHECK (vote=-1 OR vote=1)
    );""",
        """CREATE TABLE IF NOT EXISTS sessions(
        user VARCHAR(60) NOT NULL,
        cookie VARCHAR(256) NOT NULL PRIMARY KEY,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user) references users(username) ON DELETE CASCADE
    );""",
        """CREATE TABLE IF NOT EXISTS permissions(
        usertype VARCHAR(60) NOT NULL,
        `table` VARCHAR(60) NOT NULL,
        `read` BOOL DEFAULT false,
        `write` BOOL DEFAULT false,
        FOREIGN KEY (usertype) references roles(name),
        CONSTRAINT `PK_user_acces_rights` PRIMARY KEY(usertype, `table`)
    );""",
    ],
    "add_default_values": [
        mytypes.usertypes_to_mysql_insert(),
        mytypes.default_users_to_mysql_insert(),
        mytypes.rps.to_mysql_insert(),
    ],
    "search_user": "SELECT username, password FROM users WHERE username = '{username}';",
    "add_session": "INSERT INTO sessions(`user`, `cookie`) VALUES ('{username}', '{cookie}');",
    "delete_session": "DELETE FROM sessions WHERE `cookie` = '{cookie}';",
    "get_session": "SELECT `user`,`cookie` FROM sessions WHERE `cookie` = '{cookie}';",
    "add_user": "INSERT INTO users(`username`, `password`, `type`) VALUES ('{username}', '{password}', {type});",
    "delete_user": "DELETE FROM users WHERE `username` = '{username}';",
    "get_role_id": "SELECT uid FROM roles WHERE `name` = '{role}';",
    "get_permissions": (
        """SELECT t1.username, t1.usertype, t2.rolename, t3.table, t3.read, t3.write
        FROM (SELECT username, type as usertype from users) as t1
            JOIN (SELECT name AS rolename, uid AS usertype FROM roles) AS t2 ON t1.usertype = t2.usertype
                JOIN permissions AS t3 ON t2.rolename = t3.`usertype`
                    JOIN sessions ON t1.username = sessions.user
        WHERE sessions.`cookie` = '{cookie}';
        """
    ),
    "add_url": "INSERT INTO urls(`url`, `title`, `referrer`) VALUES ('{url}', '{title}', '{referrer}');",
    "get_url": "SELECT `url`, `title`, `inactive`  FROM urls WHERE {condition} AND NOT `inactive` = 1;",
    "get_url_including_inactive": "SELECT `url`, `title`, `inactive` FROM urls WHERE {condition};",
    "get_urls": "SELECT `url`, `title` FROM urls WHERE NOT `inactive` = 1;",
    "set_url": "UPDATE urls SET `{field}` = {value} WHERE `{wherefield}` = '{wherevalue}';",
    "set_vote": (
        "INSERT INTO votes(`url`, `voter`, `vote`) "
        "VALUES ('{url}', '{voter}', {vote}) ON DUPLICATE KEY UPDATE `vote` = {vote};"
    ),
    "get_url_votes": (
        "SELECT t1.`url`, totalvotes"
        " FROM urls JOIN ("
        "SELECT SUM(`vote`) as totalvotes, `url` FROM votes WHERE `url` = '{url}' GROUP BY `url`) AS t1"
        " ON urls.`url` = t1.`url` WHERE `inactive` = 0;"
    ),
    "get_all_votes": (
        "SELECT urls.url, `title`, IFNULL(`votesum`,0) as `totalvotes` FROM urls"
        " LEFT JOIN (SELECT `url`, SUM(`vote`) as `votesum` FROM votes GROUP BY `url`)"
        " AS t1 ON urls.`url` = t1.`url` WHERE urls.`inactive` = 0;"
    ),
    "get_all_users": "SELECT username, name AS role FROM (users JOIN roles ON users.type = roles.uid);",
    "get_roles": "SELECT `name` FROM roles; ",
}

if __name__ == "__main__":
    sys.exit(1)

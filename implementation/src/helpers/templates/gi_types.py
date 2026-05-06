#!/usr/bin/env python3
"""@file Contains various types defined for the exercise"""
import enum
import hashlib


class VoteType(enum.IntEnum):
    """@class Implements the enumeration type for possible votes (-1, 1)"""

    downvote = -1
    upvote = 1


class UserType(enum.Enum):
    """@class Implements the enumeration type for possible user types (roles)"""

    administrator = 0
    moderator = enum.auto()
    voter = enum.auto()
    reader = enum.auto()
    crawler = enum.auto()


class Password:
    """@class Returns a password hash, to allow secure storage (as appropriate)"""

    def __init__(self, plaintext: str):
        """@brief Class constructor

        @param[in]      plaintext       The unencrypted password
        """
        self._plaintext = plaintext
        self._hash = hashlib.sha512(plaintext.encode())

    def __str__(self) -> str:
        """@brief Returns a string representation of the hash

        @return string representation of the hash, in hexformat
        """
        return self._hash.hexdigest()

    def to_string(self) -> str:
        """@brief Returns a string representation of the hash"""
        return str(self)


class RolePermissions:
    def __init__(self):
        """@brief initialiser for RolePermissions, used to track permissions for each role"""
        self.permissions = {}

    def add_permission(self, role: UserType, table_name: str, read: bool, write: bool):
        """@brief Function to add permissions for a user

        @param[in]  role        The role to assign the permissions to
        @param[in]  table_name  The table to assign the permissions to. `db` is a special case
        @param[in]  read        If the role has read permissions for the table
        @param[in]  write       If the role has write permissions for the table
        """
        role_permissions_dict = self.permissions.setdefault(role, {})
        table_permissions_dict = role_permissions_dict.setdefault(table_name, {})
        table_permissions_dict["read"] = bool(read)
        table_permissions_dict["write"] = bool(write)

    def to_mysql_insert(
        self,
        table_name: str = "permissions",
        column_names: list[str] = ["usertype", "table", "read", "write"],
    ) -> str:
        """@brief Converts the permissions internal object to a myslq insert object

        @param[in]  permissions     The name of the table that will target the insert
        @param[in]  column_names    The names to use for the columns

        @return     query   An `INSERT` query for MySQL that will insert the items into the table
        """
        columns = ", ".join(f"`{x}`" for x in column_names)
        head = f"INSERT INTO {table_name}({columns}) VALUES"
        values = []
        for role, value in self.permissions.items():
            for table, table_permissions in value.items():
                values.append(
                    (
                        "("
                        f"'{role.name}'"
                        f", '{table}'"
                        f", {str(table_permissions['read']).lower()}"
                        f", {str(table_permissions['write']).lower()}"
                        ")"
                    ),
                )
        query = head + "\n" + ",\n".join(values) + ";"
        return query


rps = RolePermissions()

rps.add_permission(UserType.administrator, "roles", True, True)
rps.add_permission(UserType.administrator, "users", True, True)
rps.add_permission(UserType.administrator, "urls", True, True)
rps.add_permission(UserType.administrator, "votes", True, True)
rps.add_permission(UserType.administrator, "sessions", True, True)
rps.add_permission(UserType.administrator, "permissions", True, True)
# `db` is not a table but a special value
rps.add_permission(UserType.administrator, "db", True, True)
rps.add_permission(UserType.moderator, "users", True, True)
rps.add_permission(UserType.moderator, "urls", True, True)
rps.add_permission(UserType.moderator, "votes", True, False)
rps.add_permission(UserType.voter, "urls", True, False)
rps.add_permission(UserType.voter, "votes", True, True)
rps.add_permission(UserType.reader, "urls", True, False)
rps.add_permission(UserType.reader, "votes", True, False)
rps.add_permission(UserType.crawler, "urls", True, True)
rps.add_permission(UserType.crawler, "votes", True, False)


def usertypes_to_mysql_insert(table_name: str = "roles", column_names: list[str] = ["name", "uid"]):
    """@brief Returns a MySQL query using UserType as the basis to define the roles

    @param[in]  table_name      The name of the table that will target the insert
    @param[in]  column_names    The names to use for the columns
    """
    columns = ", ".join(f"`{x}`" for x in column_names)
    head = f"INSERT INTO {table_name}({columns}) VALUES"
    values = []
    for role in UserType:
        values.append(f"('{role.name}', {role.value})")

    query = head + "\n" + ",\n".join(values) + ";"
    return query


def default_users_to_mysql_insert(
    table_name: str = "users",
    column_names: list[str] = ["username", "password", "type"],
):
    """@brief Returns a MySQL query using UserType as the basis to create default users
    Users have the same username and password

    @param[in]  table_name      The name of the table that will target the insert
    @param[in]  column_names    The names to use for the columns
    """
    columns = ", ".join(f"`{x}`" for x in column_names)
    head = f"INSERT INTO {table_name}({columns}) VALUES"
    values = []

    for role in UserType:
        role.name
        role.name
        role.value
        values.append(f"('{role.name}', '{Password(role.name).to_string()}', {role.value})")

    query = head + "\n" + ",\n".join(values) + ";"
    return query

# Copyright (C) 2020 - 2021 Divkix. All rights reserved. Source code available under the AGPL.
#
# This file is part of Alita_Robot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from pyrogram import filters

from alita import DEV_USERS, OWNER_ID, SUDO_USERS


def f_dev_filter(_, __, m):
    return bool(m.from_user.id in DEV_USERS or m.from_user.id == int(OWNER_ID))


def f_sudo_filter(_, __, m):
    return bool(
        m.from_user.id in SUDO_USERS
        or m.from_user.id in DEV_USERS
        or m.from_user.id == int(OWNER_ID),
    )


dev_filter = filters.create(f_dev_filter)
sudo_filter = filters.create(f_sudo_filter)

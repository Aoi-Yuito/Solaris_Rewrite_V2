# Solaris - A Discord bot designed to make your server a safer and better place.
# Copyright (C) 2020  Ethan Henderson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Ethan Henderson
# parafoxia@carberra.xyz

import hikari
import lightbulb
from lightbulb import commands

from contextlib import redirect_stdout
from termcolor import cprint
import io, textwrap, traceback, os


sudo = lightbulb.plugins.Plugin(
    name="Sudo",
    description=None,
    include_datastore=True
)


@sudo.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    if not sudo.bot.ready.booted:
        sudo.bot.ready.up(sudo)

    sudo.d.configurable: bool = False


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="shutdown", aliases=["sd"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def shutdown_command(ctx: lightbulb.context.base.Context) -> None:
    await ctx.bot.close()


def load(bot) -> None:
    bot.add_plugin(sudo)

def unload(bot) -> None:
    bot.remove_plugin(sudo)

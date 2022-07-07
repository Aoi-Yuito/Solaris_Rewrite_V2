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


system = lightbulb.plugins.Plugin(
    name="System",
    description="System attributes.",
    include_datastore=True
)


@system.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not system.bot.ready.booted:
        system.bot.ready.up(system)

    system.d.configurable: bool = True
    system.d.image = "https://cdn.discordapp.com/attachments/991572493267636275/991586019390529536/innovation.png"


@system.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="prefix", description="Displays Solaris's prefix in your server. Note that mentioning Blue Brain will always work.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def prefix_command(ctx: lightbulb.context.base.Context) -> None:
    prefix = await ctx.bot.prefix(ctx.get_guild().id)
    await ctx.respond(
        f"{ctx.bot.info} Solaris's prefix in this server is {prefix}. To change it, use `{prefix}config system prefix <new prefix>`."
    )


def load(bot) -> None:
    bot.add_plugin(system)

def unload(bot) -> None:
    bot.remove_plugin(system)

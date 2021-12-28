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

import aiofiles
import aiofiles.os

import traceback

from solaris.utils import checks


system_err = lightbulb.plugins.Plugin(
    name="Error",
    description=None,
    include_datastore=True
)


@system_err.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not system_err.bot.ready.booted:
        system_err.bot.ready.up(system_err)

    system_err.d.configurable: bool = False
    system_err.d.image = None

    
async def error(err, guild_id, channel_id, exc_info, *args):
    ref = await record_error(err, args, exc_info)
    hub = system_err.bot.get_plugin("Hub")

    if (sc := hub.d.stdout_channel) is not None:
        if guild_id is not None:
            await sc.send(f"{system_err.bot.cross} Something went wrong (ref: {ref}).")

    if channel_id is not None:
        if guild_id is not None:
            prefix = await system_err.bot.prefix(guild_id)
            guild = await system_err.bot.rest.fetch_guild(guild_id)
            channel = guild.get_channel(channel_id)
            await channel.send(
                f"{system_err.bot.cross} Something went wrong (ref: {ref}). Quote this reference in the support server, which you can get a link for by using `{prefix}support`."
            )
        elif guild_id is None:
            await system_err.bot.rest.create_message(
                channel=channel_id,
                content=f"{system_err.bot.cross} Solaris does not support command invokations in DMs."
            )

    raise err


async def record_error(err, obj,  exc_info):
    obj = getattr(obj, "message", obj)
    if isinstance(obj, hikari.Message):
        cause = f"{obj.content}\n{obj!r}"
    else:
        cause = f"{obj!r}"

    ref = system_err.bot.generate_id()
    traceback_info = "".join(traceback.format_exception(*exc_info))
    
    await system_err.bot.db.execute(
        "INSERT INTO errors (Ref, Cause, Traceback) VALUES (?, ?, ?)", ref, cause, str(traceback_info)
    )
    return ref


@system_err.command()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="ref", description="ID of the error.", type=str)
@lightbulb.command(name="recallerror", aliases=["err"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def error_command(ctx: lightbulb.context.base.Context) -> None:
    cause, error_time, traceback = await ctx.bot.db.record(
        "SELECT Cause, ErrorTime, Traceback FROM errors WHERE Ref = ?", ctx.options.ref
    )

    path = f"{ctx.bot._dynamic}/{ctx.options.ref}.txt"
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        text = f"Time of error:\n{error_time}\n\nCause:\n{cause}\n\n{traceback}"
        await f.write(text)

    await ctx.respond(attachment=hikari.File(path))
    await aiofiles.os.remove(path)


def load(bot) -> None:
    bot.add_plugin(system_err)

def unload(bot) -> None:
    bot.remove_plugin(system_err)

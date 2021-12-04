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
from hikari import events

from solaris import Config


hub = lightbulb.plugins.Plugin(
    name="Hub",
    include_datastore=True
)


@hub.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    if not hub.bot.ready.booted:
        hub.bot.ready.up(hub)

    hub.d.configurable: bool = False

    hub.d.guild = await hub.bot.rest.fetch_guild(Config.HUB_GUILD_ID)

    if hub.d.guild is not None:
        hub.d.commands_channel = hub.d.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
        hub.d.relay_channel = hub.d.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
        hub.d.stdout_channel = hub.d.guild.get_channel(Config.HUB_STDOUT_CHANNEL_ID)

        if hub.d.stdout_channel is not None:
            await hub.d.stdout_channel.send(
                f"{hub.bot.info} Solaris is now online! (Version {hub.bot.version})"
            )


@hub.listener(events.GuildJoinEvent)
async def on_guild_join(event: events.GuildJoinEvent) -> None:
    hub.d.guild = await hub.bot.rest.fetch_guild(Config.HUB_GUILD_ID)

    if hub.d.guild is not None:
        hub.d.stdout_channel = hub.d.guild.get_channel(Config.HUB_STDOUT_CHANNEL_ID)

    guild_name = str(event.guild)

    await hub.bot.db.execute("INSERT OR IGNORE INTO system (GuildName, GuildID) VALUES (?, ?)", guild_name, event.guild_id,)
    await hub.bot.db.execute("INSERT OR IGNORE INTO gateway (GuildID) VALUES (?)", event.guild_id,)
    await hub.bot.db.execute("INSERT OR IGNORE INTO warn (GuildID) VALUES (?)", event.guild_id,)

    if hub.d.stdout_channel is not None:
        await hub.d.stdout_channel.send(
            f"{hub.bot.info} Joined guild! Nº: `{hub.bot.guild_count}` • Name: `{event.guild}` • Members: `{len(event.members):,}` • ID: `{event.guild.id}`"
        )


@hub.listener(events.GuildLeaveEvent)
async def on_guild_leave(event: events.GuildLeaveEvent) -> None:
    hub.d.guild = await hub.bot.rest.fetch_guild(Config.HUB_GUILD_ID)

    if hub.d.guild is not None:
        hub.d.stdout_channel = hub.d.guild.get_channel(Config.HUB_STDOUT_CHANNEL_ID)

    guild_name = await hub.bot.db.record("SELECT GuildName FROM system WHERE GuildID = ?", event.guild_id)

    await hub.bot.db.execute("DELETE FROM system WHERE GuildID = ?", event.guild_id)
    await hub.bot.db.execute("DELETE FROM gateway WHERE GuildID = ?", event.guild_id)
    await hub.bot.db.execute("DELETE FROM warn WHERE GuildID = ?", event.guild_id)

    if hub.d.stdout_channel is not None:
        await hub.d.stdout_channel.send(
            f"{hub.bot.info} Left guild. Name: `{guild_name[0]}` • Members: `Null` • ID: `{event.guild_id}` • Nº of guild now: `{hub.bot.guild_count}`"
        )


@hub.listener(events.GuildMessageCreateEvent)
async def on_guild_message_create(event: events.GuildMessageCreateEvent) -> None:
    hub.d.guild = await hub.bot.rest.fetch_guild(Config.HUB_GUILD_ID)

    if hub.d.guild is not None:
        hub.d.commands_channel = hub.d.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
        hub.d.relay_channel = hub.d.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
        hub.d.stdout_channel = hub.d.guild.get_channel(Config.HUB_STDOUT_CHANNEL_ID)

    server = await hub.bot.rest.fetch_guild(event.guild_id)
    channel = server.get_channel(event.channel_id)

    if event.is_bot or not event.content:
        return
        
    if server == hub.d.guild and not event.is_bot and event.author_id == 714022418200657971:
        if channel == hub.d.commands_channel:
            if event.content.startswith("shutdown") or event.content.startswith("sd"):
                await hub.bot.close()

        elif channel == hub.d.relay_channel:
            # TODO: Add relay system.
            pass



def load(bot) -> None:
    bot.add_plugin(hub)

def unload(bot) -> None:
    bot.remove_plugin(hub)

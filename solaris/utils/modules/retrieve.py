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


async def system__runfts(bot, guild_id):
    return await bot.db.field("SELECT RunFTS FROM system WHERE GuildID = ?", guild_id)


async def system__prefix(bot, guild_id):
    return await bot.db.field("SELECT Prefix FROM system WHERE GuildID = ?", guild_id)


async def system__defaultlogchannel(bot, guild_id):
    try:
        return bot.cache.get_guild_channel(await bot.db.field("SELECT DefaultLogChannelID FROM system WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def system__logchannel(bot, guild_id):
    try:
        return bot.cache.get_guild_channel(await bot.db.field("SELECT LogChannelID FROM system WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def log_channel(bot, guild_id):
    # An alias function.
    return await system__logchannel(bot, guild_id)


async def system__defaultadminrole(bot, guild_id):
    try:
        return bot.cache.get_role(await bot.db.field("SELECT DefaultAdminRoleID FROM system WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def system__adminrole(bot, guild_id):
    try:
        return bot.cache.get_role(await bot.db.field("SELECT AdminRoleID FROM system WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def gateway__active(bot, guild_id):
    return bool(await bot.db.field("SELECT Active FROM gateway WHERE GuildID = ?", guild_id))


async def gateway__ruleschannel(bot, guild_id):
    try:
        return bot.cache.get_guild_channel(await bot.db.field("SELECT RulesChannelID FROM gateway WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def gateway__gatemessage(bot, guild_id):
    try:
        rc_id, gm_id = await bot.db.record(
            "SELECT RulesChannelID, GateMessageID FROM gateway WHERE GuildID = ?", guild_id
        )
        return await bot.rest.fetch_channel(rc_id).fetch_message(gm_id)
    except hikari.NotFoundError:
        return None


async def gateway__blockingrole(bot, guild_id):
    try:
        return bot.cache.get_role(int(await bot.db.field("SELECT BlockingRoleID FROM gateway WHERE GuildID = ?", guild_id)))
    except Exception:
        return None


async def gateway__memberroles(bot, guild_id):
    if ids := await bot.db.field("SELECT MemberRoleIDs FROM gateway WHERE GuildID = ?", guild_id):
        return [bot.cache.get_role(int(id_)) for id_ in ids.split(",")]
    else:
        return []


async def gateway__exceptionroles(bot, guild_id):
    if ids := await bot.db.field("SELECT ExceptionRoleIDs FROM gateway WHERE GuildID = ?", guild_id):
        return [bot.cache.get_role(int(id_)) for id_ in ids.split(",")]
    else:
        return []


async def gateway__welcomechannel(bot, guild_id):
    try:
        return bot.cache.get_guild_channel(await bot.db.field("SELECT WelcomeChannelID FROM gateway WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def gateway__goodbyechannel(bot, guild_id):
    try:
        return bot.cache.get_guild_channel(await bot.db.field("SELECT GoodbyeChannelID FROM gateway WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def gateway__timeout(bot, guild_id):
    return await bot.db.field("SELECT Timeout FROM gateway WHERE GuildID = ?", guild_id)


async def gateway__gatetext(bot, guild_id):
    return await bot.db.field("SELECT GateText FROM gateway WHERE GuildID = ?", guild_id)


async def gateway__welcometext(bot, guild_id):
    return await bot.db.field("SELECT WelcomeText FROM gateway WHERE GuildID = ?", guild_id)


async def gateway__goodbyetext(bot, guild_id):
    return await bot.db.field("SELECT GoodbyeText FROM gateway WHERE GuildID = ?", guild_id)


async def gateway__welcomebottext(bot, guild_id):
    return await bot.db.field("SELECT WelcomeBotText FROM gateway WHERE GuildID = ?", guild_id)


async def gateway__goodbyebottext(bot, guild_id):
    return await bot.db.field("SELECT GoodbyeBotText FROM gateway WHERE GuildID = ?", guild_id)


async def warn__warnrole(bot, guild_id):
    try:
        return bot.cache.get_role(await bot.db.field("SELECT WarnRoleID FROM warn WHERE GuildID = ?", guild_id))
    except Exception:
        return None


async def warn__maxpoints(bot, guild_id):
    return await bot.db.field("SELECT MaxPoints FROM warn WHERE GuildID = ?", guild_id)


async def warn__maxstrikes(bot, guild_id):
    return await bot.db.field("SELECT MaxStrikes FROM warn WHERE GuildID = ?", guild_id)


async def warn__retroupdates(bot, guild_id):
    return await bot.db.field("SELECT RetroUpdates FROM warn WHERE GuildID = ?", guild_id)

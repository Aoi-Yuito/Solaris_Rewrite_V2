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

from solaris.utils.modules import retrieve


async def gateway(ctx):
    async with ctx.get_channel().trigger_typing():
        active, rc_id, gm_id = await ctx.bot.db.record(
            "SELECT Active, RulesChannelID, GateMessageID FROM gateway WHERE GuildID = ?", ctx.get_guild().id
        )

        if not active:
            await ctx.respond(f"{ctx.bot.cross} The gateway module is already inactive.")
        else:
            try:
                gm = await ctx.bot.cache.get_guild_channel(rc_id).fetch_message(gm_id)
                await gm.delete()
            except (hikari.NotFoundError, hikari.ForbiddenError, AttributeError):
                pass

            await ctx.bot.db.execute("DELETE FROM entrants WHERE GuildID = ?", ctx.get_guild().id)
            await ctx.bot.db.execute(
                "UPDATE gateway SET Active = 0, GateMessageID = NULL WHERE GuildID = ?", ctx.get_guild().id
            )

            await ctx.respond(f"{ctx.bot.tick} The gateway module has been deactivated.")
            lc = await retrieve.log_channel(ctx.bot, ctx.get_guild().id)
            await lc.send(f"{ctx.bot.info} The gateway module has been deactivated.")


async def everything(ctx):
    await gateway(ctx)

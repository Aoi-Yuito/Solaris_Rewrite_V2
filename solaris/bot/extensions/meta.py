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

import psutil
import datetime as dt
import typing as t
from os import name
from platform import python_version
from time import time

from solaris.utils import (
    INFO_ICON,
    LOADING_ICON,
    SUCCESS_ICON,
    SUPPORT_GUILD_INVITE_LINK,
    checks,
    chron,
    converters,
    menu,
    string,
)
from solaris.utils.modules import deactivate


class DetailedServerInfoMenu(menu.MultiPageMenu):
    def __init__(meta, ctx, table):
        pagemaps = []
        base_pm = {
            "header": "Information",
            "title": f"Detailed server information for {ctx.get_guild().name}",
            "thumbnail": ctx.get_guild().icon_url,
        }

        for key, value in table.items():
            pm = base_pm.copy()
            pm.update({"description": f"Showing {key} information.", "fields": value})
            pagemaps.append(pm)

        super().__init__(ctx, pagemaps, timeout=120.0)


class LeavingMenu(menu.SelectionMenu):
    def __init__(meta, ctx):
        pagemap = {
            "header": "Leave Wizard",
            "title": "Leaving already?",
            "description": (
                "If you remove Solaris from your server, all server information Solaris has stored, as well as any roles and channels Solaris has created, will be deleted."
                f"If you are having issues with Solaris, consider joining the support server to try and find a resolution - select {ctx.bot.info} to get an invite link.\n\n"
                "Are you sure you want to remove Solaris from your server?"
            ),
            "thumbnail": ctx.bot.get_me().avatar_url,
        }
        super().__init__(ctx, ["832160810738253834", "832160894079074335", "796345797112365107"], pagemap, timeout=120.0)

    async def start(meta):
        r = await super().start()

        if r == "confirm":
            pagemap = {
                "header": "Leave Wizard",
                "description": "Please wait... This should only take a few seconds.",
                "thumbnail": LOADING_ICON,
            }
            await meta.switch(pagemap, remove_all_reactions=True)
            await meta.leave()
        elif r == "cancel":
            await meta.stop()
        elif r == "info":
            pagemap = {
                "header": "Leave Wizard",
                "title": "Let's get to the bottom of this!",
                "description": f"Click [here]({SUPPORT_GUILD_INVITE_LINK}) to join the support server.",
                "thumbnail": INFO_ICON,
            }
            await meta.switch(pagemap, remove_all_reactions=True)

    async def leave(meta):
        dlc_id, dar_id = (
            await meta.bot.db.record(
                "SELECT DefaultLogChannelID, DefaultAdminRoleID FROM system WHERE GuildID = ?", meta.ctx.get_guild().id
            )
            or [None] * 2
        )

        await deactivate.everything(meta.ctx)

        perm = lightbulb.utils.permissions_for(
            await ctx.bot.cache.get_member(
                ctx.get_guild().id,
                841547626772168704
            )
        )
        
        if perm.MANAGE_ROLES and (dar := meta.ctx.get_guild().get_role(dar_id)) is not None:
            await dar.delete(reason="Solaris is leaving the server.")

        if (
            perm.MANAGE_CHANNELS
            and (dlc := meta.ctx.get_guild().get_channel(dlc_id)) is not None
        ):
            await dlc.delete(reason="Solaris is leaving the server.")

        pagemap = {
            "header": "Leave Wizard",
            "title": "Sorry to see you go!",
            "description": (
                f"If you ever wish to reinvite Solaris, you can do so by clicking [here]({self.bot.admin_invite}) (recommended permissions), or [here]({self.bot.non_admin_invite}) (minimum required permissions).\n\n"
                "The Solaris team wish you and your server all the best."
            ),
        }
        await meta.switch(pagemap)
        await meta.bot.rest.leave_guild(ctx.get_guild().id)


meta = lightbulb.plugins.Plugin(
    name="Meta",
    description="Commands for retrieving information regarding Solaris, from invitation links to detailed bot statistics.",
    include_datastore=True
)


@meta.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not meta.bot.ready.booted:
        #meta.d.developer = (await meta.bot.rest.fetch_application()).owner
        meta.d.developer = await meta.bot.grab_user(714022418200657971)
        meta.d.artist = await meta.bot.grab_user(714022418200657971)
        meta.d.testers = [
            (await meta.bot.grab_user(id_))
            for id_ in (
                733297588241170472,
                713882503114653746,
                735125848499421243,
                763794369714454538,
                792606073860128769,
            )
        ]
        meta.d.support_guild = await meta.bot.cache.get_guild(774530528623067157)
        meta.d.helper_role = meta.bot.cache.get_role(786614866739068938)
        
        meta.bot.ready.up(meta)

    meta.d.configurable: bool = False


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="about", aliases=["credits"], description="View info regarding those behind Solaris' development. This includes the developer and the testers.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def about_command(ctx: lightbulb.context.base.Context):
    prefix = await ctx.bot.prefix(ctx.get_guild().id)
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            title="About Solaris",
            description=f"Use `{prefix}botinfo` for detailed statistics.",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                ("Developer", meta.d.developer.mention, False),
                ("Avatar Designer", meta.d.artist.mention, False),
                ("Testers", string.list_of([t.mention for t in meta.d.testers]), False),
            ),
        )
    )


##############
@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="support", aliases=["sos"], description="Provides an invite link to Solaris' support server.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def support_command(ctx: lightbulb.context.base.Context):
    online = []
    for m in meta.d.support_guild.get_members():
        try:
            if not (await ctx.bot.grab_user(m)).is_bot:
                if ctx.bot.cache.get_presence(meta.d.support_guild.id, m).visible_status == hikari.Status.ONLINE:
                    online.append(m)
        except AttributeError:
            pass
        
    #online = [m for m in meta.d.support_guild.get_members() if not (await ctx.bot.grab_user(m)).is_bot and (ctx.bot.cache.get_presence(meta.d.support_guild.id, m)).visible_status == hikari.Status.ONLINE]
    helpers = [
        m for m in meta.d.support_guild.get_members() if not (await ctx.bot.grab_user(m)).is_bot and (ctx.bot.cache.get_member(meta.d.support_guild.id, m)).get_top_role().position == meta.d.helper_role.position
    ]
    online_helpers = set(online) & set(helpers)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description=f"Click [here]({SUPPORT_GUILD_INVITE_LINK}) to join the support server.",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                ("Online / members", f"{len(online):,} / {len(meta.d.support_guild.get_members()):,}", True),
                ("Online / helpers", f"{len(online_helpers):,} / {len(helpers):,}", True),
                ("Developer", str(ctx.bot.cache.get_presence(meta.d.support_guild.id, meta.d.developer.id).visible_status).title(), True),
            ),
        )
    )
###############


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="invite", aliases=["join"], description="Provides the links necessary to invite Solaris to other servers.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def invite_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                (
                    "Primary link",
                    f"To invite Solaris with administrator privileges, click [here]({ctx.bot.admin_invite}).",
                    False,
                ),
                (
                    "Secondary",
                    f"To invite Solaris without administrator privileges, click [here]({ctx.bot.non_admin_invite}) (you may need to grant Solaris some extra permissions in order to use some modules).",
                    False,
                ),
                ("Servers", f"{ctx.bot.guild_count:,}", True),
                ("Users", f"{ctx.bot.user_count:,}", True),
                ("Get started", "`>>setup`", True),
            ),
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="source", aliases=["src"], description="Provides a link to Solaris' source code.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def source_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                (
                    "Available under the GPLv3 license",
                    "Click [here](https://github.com/parafoxia/Solaris) to view.",
                    False,
                ),
            ),
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="issue", aliases=["bugreport", "reportbug", "featurerequest", "requestfeature"], description="Provides a link to open an issue on the Solaris repo.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def issue_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description="If you have discovered a bug not already known or want a feature not requested, open an issue using the green button in the top right of the window.",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                (
                    "View all known bugs",
                    "Click [here](https://github.com/parafoxia/Solaris/issues?q=is%3Aissue+is%3Aopen+label%3Abug).",
                    False,
                ),
                (
                    "View all planned features",
                    "Click [here](https://github.com/parafoxia/Solaris/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement).",
                    False,
                ),
            ),
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="version", description="The version to view.", required=False)
@lightbulb.command(name="changelog", aliases=["release"], description="Provides a link to view the changelog for the given version.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def changelog_command(ctx: lightbulb.context.base.Context):
    url = (
        "https://github.com/parafoxia/Solaris/releases"
        if not ctx.options.version
        else f"https://github.com/parafoxia/Solaris/releases/tag/v{ctx.options.version}"
    )
    version_info = f"version {ctx.options.version}" if ctx.options.version else "all versions"
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description=f"Click [here]({url}) to information on {version_info}.",
            thumbnail=ctx.bot.get_me().avatar_url,
        )
    )

    
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="ping", description="Ping Command")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def ping_command(ctx: lightbulb.context.base.Context):
    lat = meta.bot.heartbeat_latency * 1_000
    s = time()
    pm = await ctx.respond(f"{meta.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: - ms.")
    e = time()
    await pm.edit(
        content=f"{meta.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: {(e-s)*1_000:,.0f} ms."
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.UserBucket(300, 1))
@lightbulb.command(name="botinfo", aliases=["bi", "botstats", "stats", "bs"], description="Displays statistical information on Solaris.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def botinfo_command(ctx: lightbulb.context.base.Context):
    with (proc := psutil.Process()).oneshot():
        prefix = await ctx.bot.prefix(ctx.get_guild().id)
        uptime = time() - proc.create_time()
        cpu_times = proc.cpu_times()
        total_memory = psutil.virtual_memory().total / (1024 ** 2)
        memory_percent = proc.memory_percent()
        memory_usage = total_memory * (memory_percent / 100)

        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title="Bot information",
                description=f"Solaris was developed by {(await ctx.bot.rest.fetch_application()).owner.mention}. Use `{prefix}about` for more information.",
                thumbnail=ctx.bot.get_me().avatar_url,
                fields=(
                    ("Bot version", f"{ctx.bot.version}", True),
                    ("Python version", f"{python_version()}", True),
                    ("discord.py version", f"{hikari.__version__}", True),
                    ("Uptime", chron.short_delta(dt.timedelta(seconds=uptime)), True),
                    (
                        "CPU time",
                        chron.short_delta(
                            dt.timedelta(seconds=cpu_times.system + cpu_times.user), milliseconds=True
                        ),
                        True,
                    ),
                    (
                        "Memory usage",
                        f"{memory_usage:,.3f} / {total_memory:,.0f} MiB ({memory_percent:.0f}%)",
                        True,
                    ),
                    ("Servers", f"{ctx.bot.guild_count:,}", True),
                    ("Users", f"{ctx.bot.user_count:,}", True),
                    ("Commands", f"{ctx.bot.command_count:,}", True),
                    ("Code", f"{ctx.bot.loc.code:,} lines", True),
                    ("Comments", f"{ctx.bot.loc.docs:,} lines", True),
                    ("Blank", f"{ctx.bot.loc.empty:,} lines", True),
                    (
                        "Database calls since uptime",
                        f"{ctx.bot.db._calls:,} ({ctx.bot.db._calls/uptime:,.3f} per second)",
                        True,
                    ),
                ),
            )
        )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the User to View.", required=False)
@lightbulb.command(name="userinfo", aliases=["ui"], description="Displays information on a given user. If no user is provided, Solaris will display your information.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def userinfo_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target or ctx.author

    if isinstance(target, hikari.Member):
        ps = target.premium_since
        ngr = len(ctx.get_guild().get_roles())
        
        perm = lightbulb.utils.permissions_for(
            await ctx.bot.cache.get_member(
                ctx.get_guild().id,
                target.id
            )
        )

        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"User information for {target.username}",
                description=(
                    f"This member is also known as {target.display_name} in this server."
                    if target.nickname
                    else f"This member does not have a nickname in this server."
                ),
                colour=target.get_top_role().color,
                thumbnail=target.avatar_url,
                fields=(
                    ("ID", target.id, False),
                    ("Discriminator", target.discriminator, True),
                    ("Bot?", target.is_bot, True),
                    ("Admin?", "True" if perm.ADMINISTRATOR else "False", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Joined on", chron.long_date(target.joined_at), True),
                    ("Boosted on", chron.long_date(ps) if ps else "-", True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                    ("Member for", chron.short_delta(dt.datetime.utcnow() - target.joined_at), True),
                    ("Booster for", chron.short_delta(dt.datetime.utcnow() - ps) if ps else "-", True),
                    ("Status", str((ctx.bot.cache.get_presence(ctx.get_guild().id, target.id)).visible_status).title() if (ctx.bot.cache.get_presence(ctx.get_guild().id, target.id)) else "offline", True),
                    (
                        "Activity type",
                        str(target.activity.type).title().split(".")[-1] if target.activity is not None else "-",
                        True,
                    ),
                    ("Activity name", target.activity.name if target.activity else "-", True),
                    ("Nº of roles", f"{len(target.get_roles())-1:,}", True),
                    ("Top role", target.get_top_role().mention, True),
                    ("Top role position", f"{string.ordinal(ngr - target.get_top_role().position)} / {ngr:,}", True),
                ),
            )
        )

    elif isinstance(target, hikari.User):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"User information for {target.username}",
                description="Showing reduced information as the given user is not in this server.",
                thumbnail=target.avatar_url,
                fields=(
                    ("ID", target.id, True),
                    ("Discriminator", target.discriminator, True),
                    ("Bot?", target.is_bot, True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                    ("\u200b", "\u200b", True),
                ),
            )
        )

    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a user with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.UserBucket(10, 1))
@lightbulb.command(name="h", description="get help text")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def h_command(ctx: lightbulb.context.base.Context):
    """get help text"""
        #await ctx.send_help(ctx.command)  
        #help_text = lightbulb.get_help_text(self.h_command)
        #await ctx.respond(help_text)
        
        #from bluebrain.utils.modules import retrieve
        #await ctx.respond((await retrieve.log_channel(ctx.bot, ctx.get_guild().id)))
        
        #bot = await self.bot.rest.fetch_member(ctx.get_guild().id, 841547626772168704)
        #perm = lightbulb.utils.permissions_for(bot)
        #print(perm.ADMINISTRATOR)

        #async with ctx.get_channel().trigger_typing():
        #    msg = await ctx.respond("test")
        #    emoji = []
        #    emoji.append(ctx.bot.cache.get_emoji(832160810738253834))
        #    emoji.append(ctx.bot.cache.get_emoji(832160894079074335))   
        #    for em in emoji:
        #await msg.add_reaction(em)

        #perm = lightbulb.utils.permissions_in(
        #    ctx.get_channel(),
        #    await ctx.bot.rest.fetch_member(
        #        ctx.get_guild().id,
        #        841547626772168704
        #    ),
        #    True
        #)
        #if not perm:
        #    print(perm.SEND_MESSAGES)

        #perm = lightbulb.utils.permissions_for(
        #    await ctx.bot.rest.fetch_member(
        #        ctx.get_guild().id,
        #        841547626772168704
        #    )
        #)
        #print(perm)
        #for ext in self.bot._extensions:
        #    await ctx.respond(self.bot.get_plugin(ext.title()))
    await ctx.respond(ctx.get_guild().id)
    l = [m for m in ctx.get_guild().get_members()]
    await ctx.respond(l)
    await ctx.respond(ctx.bot.cache.get_presence(ctx.get_guild().id, ctx.author.id).activities)
    #p = []
    #for m in ctx.get_guild().get_members():
    #    p.append(ctx.bot.cache.get_presence(ctx.get_guild().id, m))
    #await ctx.respond(p)
    #r = []
    #for m in ctx.get_guild().get_members():
    #    r.append(ctx.bot.cache.get_member(ctx.get_guild().id, m).get_top_role().position)
    #await ctx.respond(r)



def load(bot):
    bot.add_plugin(meta)

def unload(bot):
    bot.remove_plugin(meta)

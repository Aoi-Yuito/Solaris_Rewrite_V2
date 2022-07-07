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

import datetime as dt
import typing as t
from collections import defaultdict

import hikari
import lightbulb
from apscheduler.triggers.cron import CronTrigger
from lightbulb import commands

from solaris.utils import checks, chron, string, trips

MODULE_NAME = "gateway"


def format_custom_message(text, member):
    if text:
        guild = gateway.bot.cache.get_guild(member.guild_id)
        bot_count = len([m for m in guild.get_members() if gateway.bot.cache.get_member(member.guild_id, m).is_bot])
        human_count = guild.member_count - bot_count

        # Contains U+200E character.
        return "‎" + string.safe_format(
            text,
            membername=member.name,
            username=member.username,
            membermention=member.mention,
            usermention=member.mention,
            memberstr=str(member),
            userstr=str(member),
            memberid=member.id,
            userid=member.id,
            servername=guild.name,
            guildname=guild.name,
            serverid=guild.id,
            guildid=guild.id,
            membercount=guild.member_count,
            ordmembercount=string.ordinal(guild.member_count),
            humancount=human_count,
            ordhumancount=string.ordinal(human_count),
            botcount=bot_count,
            ordbotcount=string.ordinal(bot_count),
        )

async def allow_on_accept(bot, member, okay, br_id, mr_ids, wc_id, wt):
    if (br := await okay.blocking_role(br_id)) in member.get_roles():
        if (mrs := await okay.member_roles(mr_ids)) and (unassigned := set(mrs) - set(member.get_roles())):
            for r in list(unassigned):
                await member.add_role(role=r, reason="Member accepted the server rules.")
        await member.remove_role(role=br, reason="Member accepted the server rules.")

        if wc := await okay.welcome_channel(wc_id):
            await wc.send(
                format_custom_message(wt, member)
                or f"‎{bot.info} {member.mention} joined the server and accepted the rules. Welcome!"
            )

        await gateway.bot.db.execute(
            "DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", member.guild_id, member.id
        )

    await gateway.bot.db.execute("INSERT OR IGNORE INTO accepted VALUES (?, ?)", member.guild_id, member.id)

async def remove_on_decline(member, okay, br_id):
    if (br := await okay.blocking_role(br_id)) in member.get_roles():
        await member.kick(reason="Member declined the server rules.")

async def allow_on_exception(member, okay, br_id, mr_ids):
    if (br := await okay.blocking_role(br_id)) in member.get_roles():
        if (mrs := await okay.member_roles(mr_ids)) and (unassigned := set(mrs) - set(member.get_roles())):
            for r in list(unassigned):
                await member.add_role(role=r, reason="Member was given an exception role.")
        await member.remove_role(br, reason="Member was given an exception role.")

        await gateway.bot.db.execute(
            "DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", member.guild_id, member.id
        )


async def remove_on_timeout(gateway):
    if gateway.bot.ready.gateway:
        time_outs = {}

        for guild_id, user_id in await gateway.bot.db.records(
            "SELECT GuildID, UserID FROM entrants WHERE CURRENT_TIMESTAMP > Timeout"
        ):
            time_outs.setdefault(guild_id, []).append(user_id)

        for guild_id, user_ids in time_outs.items():
            guild = gateway.bot.cache.get_guild(guild_id)
            br = await Okay(gateway.bot, guild).blocking_role(
                await gateway.bot.db.field("SELECT BlockingRoleID FROM gateway WHERE GuildID = ?", guild_id)
            )

            for user_id in user_ids:
                if br in (member := guild.get_member(user_id)).get_roles():
                    await member.kick(reason="Member failed to accept the server rules before being timed out.")


class Okay:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

    async def permissions(self):
        bot_user = self.bot.cache.get_member(self.guild.id, 841547626772168704)
        perm = lightbulb.utils.permissions_for(bot_user)
        
        if perm.MANAGE_ROLES is None:
            await trips.gateway(self, "Solaris no longer has the Manage Roles permission")
        elif perm.KICK_MEMBERS is None:
            await trips.gateway(self, "Solaris no longer has the Kick Members permission")
        else:
            return True

    async def gate_message(self, rc_id, gm_id):
        try:   
            if (rc := self.bot.cache.get_guild_channel(rc_id)) is None:
                await trips.gateway(self, "the rules channel no longer exists, or is unable to be accessed by Solaris")
            else:
                # This is done here to ensure the correct order of operations.
                gm = await self.bot.rest.fetch_message(rc_id, gm_id)

                perm = lightbulb.utils.permissions_in(
                    rc,
                    self.bot.cache.get_member(
                        self.guild.id,
                        841547626772168704
                    ),
                    True
                )

                if perm.MANAGE_MESSAGES is None:
                    await trips.gateway(
                        self, "Solaris does not have the Manage Messages permission in the rules channel"
                    )
                else:
                    return gm

        except hikari.NotFoundError:
            await trips.gateway(self, "the gate message no longer exists")

    async def blocking_role(self, br_id):
        bot_user = self.bot.cache.get_member(self.guild.id, 841547626772168704)
        
        if (br := self.bot.cache.get_role(br_id)) is None:
            await trips.gateway(self, "the blocking role no longer exists, or is unable to be accessed by Solaris")
        elif br.position >= bot_user.get_top_role().position:
            await trips.gateway(
                self, "the blocking role is equal to or higher than Solaris' top role in the role hierarchy"
            )
        else:
            return br

    async def member_roles(self, mr_ids):
        if mr_ids is not None:
            bot_user = self.bot.cache.get_member(self.guild.id, 841547626772168704)
            
            for r in (mrs := [self.bot.cache.get_role(int(id_)) for id_ in mr_ids.split(",")]) :
                if r is None:
                    await trips.gateway(
                        self, "one or more member roles no longer exist, or are unable to be accessed by Solaris"
                    )
                    return
                elif r.position >= bot_user.get_top_role().position:
                    await trips.gateway(
                        self,
                        "one or more member roles are equal to or higher than Solaris' top role in the role hierarchy",
                    )
                    return

            return mrs

    async def exception_roles(self, er_ids):
        if er_ids is not None:
            for r in (ers := [self.bot.cache.get_role(int(id_)) for id_ in er_ids.split(",")]) :
                if r is None:
                    await trips.gateway(
                        self, "one or more exception roles no longer exist, or are unable to be accessed by Solaris"
                    )
                    return

            return ers

    async def welcome_channel(self, wc_id):
        if wc_id is not None:
            if (wc := self.bot.cache.get_guild_channel(wc_id)) is None:
                await trips.gateway(
                    self, "the welcome channel no longer exists or is unable to be accessed by Solaris"
                )
            perm = lightbulb.utils.permissions_in(
                wc,
                self.bot.cache.get_member(
                    self.guild.id,
                    841547626772168704
                ),
                True
            )

            if perm.SEND_MESSAGES is None:
                await trips.gateway(self, "Solaris does not have the Send Messages permission in the welcome channel")
            else:
                return wc

    async def goodbye_channel(self, gc_id):
        if gc_id is not None:
            if (gc := self.bot.cache.get_guild_channel(gc_id)) is None:
                await trips.gateway(
                    self, "the goodbye channel no longer exists or is unable to be accessed by Solaris"
                )

            perm = lightbulb.utils.permissions_in(
                gc,
                self.bot.cache.get_member(
                    self.guild.id,
                    841547626772168704
                ),
                True
            )
            
            if perm.SEND_MESSAGES is None:
                await trips.gateway(self, "Solaris does not have the Send Messages permission in the goodbye channel")
            else:
                return gc


class Synchronise:
    def __init__(self, bot):
        self.bot = bot

    async def _allow(self, okay, member, br_id, mr_ids):
        if (mrs := await okay.member_roles(mr_ids)) and (unassigned := set(mrs) - set(member.get_roles())):
            for r in list(unassigned):
                await member.add_role(
                    role=r,
                    reason="Member accepted the server rules (performed during synchronisation)."
                )

        if (br := await okay.blocking_role(br_id)) in member.get_roles():
            await member.remove_role(
                br,
                reason="Member accepted the server rules, or was given an exception role (performed during synchronisation).",
            )

    async def _deny(self, okay, member, br_id):
        await member.kick(reason="Member declined the server rules (performed during synchronisation).")

    async def members(self, guild, okay, gm, br_id, mr_ids, er_ids, last_commit, entrants, accepted):
        def _check(m):
            return not m.is_bot and (m.joined_at.replace(tzinfo=None) > last_commit or m.id in entrants)

        reacted = []
        new = []
        left = []

        ticked = [u.id async for u in self.bot.rest.fetch_reactions_for_emoji(gm.channel_id, gm.id, gm.reactions[0].emoji.name, gm.reactions[0].emoji.id)]
        crossed = [u.id async for u in self.bot.rest.fetch_reactions_for_emoji(gm.channel_id, gm.id, gm.reactions[1].emoji.name, gm.reactions[1].emoji.id)]
        ers = await okay.exception_roles(er_ids) or []

        for member in filter(lambda m: _check(guild.get_member(m)), guild.get_members()):
            if member.id in ticked:
                await self._allow(okay, member, br_id, mr_ids)
                reacted.append((guild.id, member.id))
                new.append((guild.id, member.id))
            elif member in crossed:
                await self._deny(okay, member, br_id)
                reacted.append((guild.id, member.id))
            elif any(r in member.get_roles() for r in ers):
                await self._allow(okay, member, br_id, mr_ids)
                reacted.append((guild.id, member.id))

        for user_id in set([*entrants, *accepted]):
            if not guild.get_member(user_id):
                left.append((guild.id, user_id))

        await self.bot.db.executemany("DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", set([*reacted, *left]))
        await self.bot.db.executemany("DELETE FROM accepted WHERE GuildID = ? AND UserID = ?", set(left))
        await self.bot.db.executemany("INSERT OR IGNORE INTO accepted VALUES (?, ?)", set(new))

    async def roles(self, guild, okay, br_id, mr_ids, accepted, accepted_only):
        def _check(m):
            return not m.is_bot and (not accepted_only or m.id in accepted)

        br = await okay.blocking_role(br_id)
        mrs = await okay.member_roles(mr_ids)

        for member in filter(lambda m: _check(guild.get_member(m)), guild.get_members()):
            if br not in guild.get_member(member).get_roles() and (unassigned := set(mrs) - set(guild.get_member(member).get_roles())):
                for r in list(unassigned):
                    await member.add_role(
                        role=r,
                        reason="Member roles have been updated (performed during synchronisation)."
                    )

    async def reactions(self, guild, gm, accepted):
        tick = gm.reactions[0]
        cross = gm.reactions[1]
        ticked = [u.id async for u in self.bot.rest.fetch_reactions_for_emoji(gm.channel_id, gm.id, gm.reactions[0].emoji.name, gm.reactions[0].emoji.id)]
        crossed = [u.id async for u in self.bot.rest.fetch_reactions_for_emoji(gm.channel_id, gm.id, gm.reactions[1].emoji.name, gm.reactions[1].emoji.id)]
        ticked_and_left = set(ticked) - set([m for m in guild.get_members()])
        crossed_and_left = set(crossed) - set([m for m in guild.get_members()])

        for user in ticked_and_left:
            await gm.remove_reaction(emoji=gm.reactions[0].emoji.name, emoji_id=gm.reactions[0].emoji.id, user=user)

        for user in crossed_and_left:
            await gm.remove_reaction(emoji=gm.reactions[1].emoji.name, emoji_id=gm.reactions[1].emoji.id, user=user)

        for user in crossed:
            if user in accepted:
                await gm.remove_reaction(emoji=gm.reactions[1].emoji.name, emoji_id=gm.reactions[1].emoji.id, user=user)

    async def on_boot(self):
        last_commit = chron.from_iso(await self.bot.db.field("SELECT Value FROM bot WHERE Key = 'last commit'"))
        records = await self.bot.db.records(
            "SELECT GuildID, RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE Active = 1"
        )

        entrants = {
            guild_id: [int(user_id) for user_id in user_ids.split(",")]
            for guild_id, user_ids in await self.bot.db.records(
                "SELECT GuildID, GROUP_CONCAT(UserID) FROM entrants GROUP BY GuildID"
            )
        }

        accepted = {
            guild_id: [int(user_id) for user_id in user_ids.split(",")]
            for guild_id, user_ids in await self.bot.db.records(
                "SELECT GuildID, GROUP_CONCAT(UserID) FROM accepted GROUP BY GuildID"
            )
        }

        for guild_id, rc_id, gm_id, br_id, mr_ids, er_ids in records:
            guild = self.bot.cache.get_guild(guild_id)
            okay = Okay(self.bot, guild)

            if gm := await okay.gate_message(rc_id, gm_id):
                await self.members(
                    guild,
                    okay,
                    gm,
                    br_id,
                    mr_ids,
                    er_ids,
                    last_commit,
                    entrants.get(guild_id, []),
                    accepted.get(guild_id, []),
                )

        await self.bot.db.execute("UPDATE entrants SET Timeout = datetime('now', '+3600 seconds')")


gateway = lightbulb.plugins.Plugin(
    name="Gateway",
    description="Controls and monitors the flow of members in and out of your server. When active, members are forced to accept the server rules before gaining full access to the server.",
    include_datastore=True
)


@gateway.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not gateway.bot.ready.booted:
        gateway.bot.ready.up(gateway)

    gateway.d.configurable: bool = True
    gateway.bot.scheduler.add_job(remove_on_timeout, CronTrigger(second=0), args=[gateway])
    gateway.d.image = "https://cdn.discordapp.com/attachments/991572493267636275/991586966372094002/network.png"


@gateway.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent):
    if gateway.bot.ready.gateway:
        okay = Okay(gateway.bot, gateway.bot.cache.get_guild(event.guild_id))
        active, br_id, wc_id, timeout, wbt = (
            await gateway.bot.db.record(
                "SELECT Active, BlockingRoleID, WelcomeChannelID, Timeout, WelcomeBotText FROM gateway WHERE GuildID = ?",
                event.guild_id,
            )
            or [None] * 7
        )

        if active and await okay.permissions():
            if event.member.is_bot:
                if wc := await okay.welcome_channel(wc_id):
                    await wc.send(
                        format_custom_message(wbt, event.member)
                        or f"‎{gateway.bot.info} The bot {member.mention} was added to the server."
                    )
            else:
                if br := await okay.blocking_role(br_id):
                    await event.member.add_role(br, reason="Needed to enforce a decision on the server rules.")
                    await gateway.bot.db.execute(
                        "INSERT INTO entrants VALUES (?, ?, ?)",
                        event.guild_id,
                        event.member.id,
                        chron.to_iso(event.member.joined_at + dt.timedelta(seconds=timeout or 300)),
                    )

@gateway.listener(hikari.MemberDeleteEvent)
async def on_member_remove(event: hikari.MemberDeleteEvent):
    if gateway.bot.ready.gateway:
        okay = Okay(gateway.bot, gateway.bot.cache.get_guild(event.guild_id))
        active, rc_id, gm_id, gc_id, gt, gbt = (
            await gateway.bot.db.record(
                "SELECT Active, RulesChannelID, GateMessageID, GoodbyeChannelID, GoodbyeText, GoodbyeBotText FROM gateway WHERE GuildID = ?",
                event.guild_id,
            )
            or [None] * 4
        )

        if active:
            print(event.old_member)
            if event.old_member.is_bot:
                if gc := await okay.goodbye_channel(gc_id):
                    await gc.send(
                        format_custom_message(gbt, event.old_member)
                        or f'{gateway.bot.info} ‎The bot "{event.old_member.username}" was removed from the server.'
                    )
            else:
                if await gateway.bot.db.field(
                    "SELECT UserID FROM entrants WHERE GuildID = ? AND UserID = ?", event.guild_id, event.user_id
                ):
                    await gateway.bot.db.execute(
                        "DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", event.guild_id, event.user_id
                    )
                elif gc := await okay.goodbye_channel(gc_id):
                    await gc.send(
                        format_custom_message(gt, event.old_member)
                        or f"{gateway.bot.info} ‎{event.old_member.username} is no longer in the server."
                    )

                await gateway.bot.db.execute(
                    "DELETE FROM accepted WHERE GuildID = ? AND UserID = ?", event.guild_id, event.user_id
                )

                #if (gm := await okay.gate_message(rc_id, gm_id)) :
                    #for emoji in self.bot.emoji.get_many("confirm", "cancel"):
                        #try:
                            #await gm.remove_reaction(emoji, member)
                        #except discord.NotFound:
                            # In the rare instance the module trips while attempting to remove a reaction.
                            #pass


@gateway.listener(hikari.MemberUpdateEvent)
async def on_member_update(event: hikari.MemberUpdateEvent):
    if gateway.bot.ready.gateway and len([i for i in event.member.role_ids]) > len([i for i in event.old_member.role_ids]):
        okay = Okay(gateway.bot, gateway.bot.cache.get_guild(event.guild_id))
        active, br_id, mr_ids, er_ids = (
            await gateway.bot.db.record(
                "SELECT Active, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE GuildID = ?",
                event.guild_id,
            )
            or [None] * 4
        )

        if active and er_ids:
            added_role = (set([r for r in event.member.get_roles()]) - set([r for r in event.old_member.get_roles()])).pop()

            ers = await okay.exception_roles(er_ids)
            if ers is not None and added_role in ers:
                await allow_on_exception(after, okay, br_id, mr_ids)

@gateway.listener(hikari.GuildReactionAddEvent)
async def on_raw_reaction_add(event: hikari.GuildReactionAddEvent):
    if gateway.bot.ready.gateway:
        okay = Okay(gateway.bot, gateway.bot.cache.get_guild(event.guild_id))
        active, rc_id, gm_id, br_id, mr_ids, wc_id, wt = (
            await gateway.bot.db.record(
                "SELECT Active, RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, WelcomeChannelID, WelcomeText FROM gateway WHERE GuildID = ?",
                event.guild_id,
            )
            or [None] * 7
        )

        if active == 1 and event.message_id == gm_id and (gm := await okay.gate_message(rc_id, gm_id)):
            if event.emoji_id == gateway.bot.cache.get_emoji(832160810738253834).id: # Accept emoji ID 832160810738253834
                await allow_on_accept(gateway.bot, event.member, okay, br_id, mr_ids, wc_id, wt)
            elif event.emoji_id == gateway.bot.cache.get_emoji(832160894079074335).id: # Cancel emoji ID 832160894079074335
                await remove_on_decline(event.member, okay, br_id)


@gateway.command()
#@checks.author_can_configure()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="synchronise", aliases=["synchronize", "sync"], description="Synchronise the gateway module. Use the command for information on available subcommands.",)
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def synchronise_group(ctx: lightbulb.context.base.Context) -> None:
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Synchronise",
            description="There are a few different syncing methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help synchronise {cmd.name}`",
                        False,
                    )
                    for cmd in (*cmds[1:], cmds[0])  # Order them properly.
                ),
                (
                    "Why does the module need synchronising?",
                    "Generally speaking, it will not 99% of the time, especially as Solaris performs an automatic synchronisation on start-up. However, due to the complexity of the systems used, and measures taken to make sure there are no database conflicts, it can fall out of sync sometimes. This command is the solution to that problem.",
                    False,
                ),
            ),
        )
    )


@synchronise_group.child()
#@checks.author_can_configure()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(3600, 1))
@lightbulb.command(name="members", description="Handles offline arrivals and departures. This is generally not required as Solaris does this on start-up.",)
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def synchronise_members_command(ctx: lightbulb.context.base.Context) -> None:
    async with ctx.get_channel().trigger_typing():
        okay = Okay(ctx.bot, ctx.get_guild())
        rc_id, gm_id, br_id, mr_ids, er_ids = (
            await ctx.bot.db.record(
                "SELECT RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE GuildID = ?",
                ctx.guild_id,
            )
            or [None] * 5
        )
        last_commit = chron.from_iso(await ctx.bot.db.field("SELECT Value FROM bot WHERE Key = 'last commit'"))
        entrants = await ctx.bot.db.column("SELECT UserID FROM entrants WHERE GuildID = ?", ctx.guild_id)
        accepted = await ctx.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild_id)

        if gm := await okay.gate_message(rc_id, gm_id):
            await Synchronise(ctx.bot).members(
                ctx.get_guild(), okay, gm, br_id, mr_ids, er_ids, last_commit, entrants, accepted
            )
            await ctx.respond(f"{ctx.bot.tick} Server members synchronised.")


@synchronise_group.child()
#@checks.author_can_configure()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(3600, 1))
@lightbulb.option(name="accepted_only", description="Synchronise roles only.", type=bool, required=False, default=True)
@lightbulb.command(name="roles", description="Provides the member roles to those who have accepted the rules. This is good to run after you add a new member role, but Solaris will not remove roles that are no longer member roles. If `accepted_only` is set to `False`, every single member will receive these roles regardless of any other factors.",)
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def synchronise_roles_command(ctx: lightbulb.context.base.Context) -> None:
    async with ctx.get_channel().trigger_typing():
        okay = Okay(ctx.bot, ctx.get_guild())
        br_id, mr_ids = (
            await ctx.bot.db.record(
                "SELECT BlockingRoleID, MemberRoleIDs FROM gateway WHERE GuildID = ?", ctx.guild_id,
            )
            or [None] * 2
        )
        accepted = await ctx.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild_id)

        await Synchronise(ctx.bot).roles(ctx.get_guild(), okay, br_id, mr_ids, accepted, ctx.options.accepted_only)
        await ctx.respond(f"{ctx.bot.tick} Member roles synchronised.")


@synchronise_group.child()
#@checks.author_can_configure()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(86400, 1))
@lightbulb.command(name="reactions", description="Synchronises the reactions on the gate message. This is useful if you only want to view reactions for current members, but as this is an expensive operation in large servers, you can only do this once every 24 hours.",)
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def synchronise_reactions_command(ctx: lightbulb.context.base.Context) -> None:
    async with ctx.get_channel().trigger_typing():
        okay = Okay(ctx.bot, ctx.get_guild())
        rc_id, gm_id = (
            await ctx.bot.db.record(
                "SELECT RulesChannelID, GateMessageID FROM gateway WHERE GuildID = ?", ctx.guild_id,
            )
            or [None] * 2
        )
        accepted = await ctx.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild_id)

        if gm := await okay.gate_message(rc_id, gm_id):
            await Synchronise(ctx.bot).reactions(ctx.get_guild(), gm, accepted)
            await ctx.respond(f"{ctx.bot.tick} Gate message reactions synchronised.")


@synchronise_group.child()
#@checks.author_can_configure()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(86400, 1))
@lightbulb.option(name="roles_for_accepted_only", description="Synchronise everything.", type=bool, required=False, default=True)
@lightbulb.command(name="everything", aliases=["full", "all"], description="Does all of the above. Read the help descriptions for the other commands in this group for more information.",)
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def synchronise_everything_command(ctx: lightbulb.context.base.Context) -> None:
    async with ctx.get_channel().trigger_typing():
        okay = Okay(ctx.bot, ctx.get_guild())
        rc_id, gm_id, br_id, mr_ids, er_ids = (
            await ctx.bot.db.record(
                "SELECT RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE GuildID = ?",
                ctx.guild_id,
            )
            or [None] * 5
        )
        last_commit = chron.from_iso(await ctx.bot.db.field("SELECT Value FROM bot WHERE Key = 'last commit'"))
        entrants = await ctx.bot.db.column("SELECT UserID FROM entrants WHERE GuildID = ?", ctx.guild_id)
        accepted = await ctx.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild_id)

        if gm := await okay.gate_message(rc_id, gm_id):
            sync = Synchronise(ctx.bot)
            await sync.members(ctx.get_guild(), okay, gm, br_id, mr_ids, er_ids, last_commit, entrants, accepted)
            await sync.roles(ctx.get_guild(), okay, br_id, mr_ids, accepted, ctx.options.roles_for_accepted_only)
            await sync.reactions(ctx.get_guild(), gm, accepted)
            await ctx.respond(f"{ctx.bot.tick} Gateway module fully synchronised.")


@gateway.command()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Name of the target to inspect.", type=hikari.Member, required=False)
@lightbulb.command(name="checkaccepted", aliases=["ca"], description='Checks whether a given user has accepted the server rules. If no user is provided, Solaris will display the total number of members who have accepted. A member who has "accepted" is taken as one who has reacted to the gate message with the confirm emoji at some point, regardless of whether they unreacted later. The only exceptions to this are if the member leaves the server, or if the acceptance records are manually reset.',)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def checkaccepted_command(ctx: lightbulb.context.base.Context) -> None:
    if ctx.options.target is not None:
        if await ctx.bot.db.field(
            "SELECT UserID FROM accepted WHERE GuildID = ? AND UserID = ?", ctx.guild_id, ctx.options.target.id
        ):
            await ctx.respond(f"{ctx.bot.tick} {ctx.options.target.username} has accepted the server rules.")
        else:
            await ctx.respond(f"{ctx.bot.cross} {ctx.options.target.username} has not accepted the server rules.")
    else:
        accepted = await ctx.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild_id)
        await ctx.respond(
            f"{ctx.bot.info} {len(accepted):,} / {len([m for m in ctx.get_guild().get_members() if not ctx.get_guild().get_member(m).is_bot]):,} members have accepted the server rules."
        )


@gateway.command()
#@checks.author_can_configure()
#@checks.module_is_active(MODULE_NAME)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
@lightbulb.command(name="resetaccepted", description="Resets Solaris' records regarding who has accepted the rules in your server. This action is irreversible.",)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def resetaccepted_command(ctx: lightbulb.context.base.Context) -> None:
    await ctx.bot.db.execute("DELETE FROM accepted WHERE GuildID = ?", ctx.guild_id)
    await ctx.respond(f"{ctx.bot.tick} Acceptance records for this server have been reset.")


def load(bot) -> None:
    bot.add_plugin(gateway)

def unload(bot) -> None:
    bot.remove_plugin(gateway)

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

from solaris.utils.menu import selectors


class Menu:
    def __init__(self, ctx, pagemap, *, delete_after=False, delete_invoke_after=None):
        self.ctx = ctx
        self.bot = ctx.bot
        self.pagemap = pagemap
        self.delete_after = delete_after
        self.delete_invoke_after = delete_invoke_after or delete_after

    async def start(self):
        resp = await self.ctx.respond(embed=self.bot.embed.build(ctx=self.ctx, **self.pagemap))
        self.message = await resp.message()

    async def stop(self):
        if self.delete_after:
            await self.message.delete()
        else:
            await self.message.remove_all_reactions()
            await self.message.edit(content=f"{self.bot.info} The interactive menu was closed.", embed=None)

        if self.delete_invoke_after:
            await self.ctx.message.delete()

    async def timeout(self, length):
        if self.delete_after:
            await self.message.delete()
        else:
            await self.message.remove_all_reactions()
            await self.message.edit(
                content=f"{self.bot.info} The interactive menu timed out as there was no user interaction for {length}.",
                embed=None,
            )

        if self.delete_invoke_after:
            await self.ctx.message.delete()

    async def switch(self, pagemap=None, remove_all_reactions=False):
        if remove_all_reactions:
            await self.message.remove_all_reactions()

        await self.message.edit(embed=self.bot.embed.build(ctx=self.ctx, **(pagemap or self.pagemap)))

    def __repr__(self):
        return (
            f"<Menu"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )


class SelectionMenu(Menu):
    def __init__(
        self,
        ctx,
        selection,
        pagemap,
        *,
        delete_after=False,
        delete_invoke_after=None,
        timeout=300.0,
        auto_exit=True,
        check=None,
    ):
        super().__init__(ctx, pagemap, delete_after=delete_after, delete_invoke_after=delete_invoke_after)
        self.selector = selectors.Selector(self, selection, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self):
        await super().start()
        return await self.selector.response()

    def __repr__(self):
        return (
            f"<SelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )


class NumberedSelectionMenu(Menu):
    def __init__(
        self,
        ctx,
        iterable,
        pagemap,
        *,
        delete_after=False,
        delete_invoke_after=None,
        timeout=300.0,
        auto_exit=True,
        check=None,
    ):
        super().__init__(ctx, pagemap, delete_after=delete_after, delete_invoke_after=delete_invoke_after)
        self.selector = selectors.NumericalSelector(self, iterable, timeout=timeout, auto_exit=auto_exit, check=check)

    @property
    async def page_field(self):
        return (f"{self.selector.page_info}", f"{await self.selector.table}", False)

    async def start(self):
        self.pagemap.update({"fields": (await self.page_field,)})
        await super().start()
        return await self.selector.response()

    async def switch(self, emoji_name, emoji_id):
        self.pagemap.update({"fields": (await self.page_field,)})
        await super().switch()
        await self.message.remove_reaction(emoji=emoji_name, emoji_id=emoji_id, user=self.ctx.author)

    def __repr__(self):
        return (
            f"<NumberedSelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )


class MultiPageMenu(Menu):
    def __init__(
        self, ctx, pagemaps, *, delete_after=False, delete_invoke_after=None, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(ctx, pagemaps[0], delete_after=delete_after, delete_invoke_after=delete_invoke_after)
        self.selector = selectors.PageControls(self, pagemaps, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self):
        await super().start()
        return await self.selector.response()

    async def switch(self, emoji_name, emoji_id):
        await super().switch(self.selector.pagemaps[self.selector.page])
        await self.message.remove_reaction(emoji=emoji_name, emoji_id=emoji_id, user=self.ctx.author)

    def __repr__(self):
        return (
            f"<MultiPageMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )
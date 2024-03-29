from discord.ext import commands
import discord


def get_colour():
    return discord.Colour.blurple()


default_help = """
***Voice Commands***
`{prefix}voice lock`
`{prefix}voice unlock`
`{prefix}voice ghost`
`{prefix}voice unghost`
`{prefix}voice ghostmen`
`{prefix}voice bitrate`
`{prefix}voice name`
`{prefix}voice permit/allow`
`{prefix}voice deny/reject`
`{prefix}voice game`
`{prefix}voice limit`
`{prefix}voice claim`
`{prefix}voice transfer`
`{prefix}voice ban`
`{prefix}voice unban`
`{prefix}voice block`
`{prefix}voice unblock`

***Setup Commands***
`{prefix}setprefix`
`{prefix}voice setup`
`{prefix}voice setup clone`
`{prefix}voice setup sequence`
`{prefix}voice setup predefined`

***General Commands***
`{prefix}ping`
`{prefix}uptime`
`{prefix}invite`
`{prefix}support`
`{prefix}source [command]`
"""


class MyHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={"help": "Shows help about the bot, a command"})

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error.original))

    def get_command_signature(self, command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = "/".join(command.aliases)
            fmt = f"[{command.name}/{aliases}]"
            if parent:
                fmt = f"{parent} {fmt}"
            alias = fmt
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature.replace('_', ' ')}"

    async def send_bot_help(self, mapping):
        bot = self.context.bot
        entries = sorted(bot.commands, key=lambda x: x.qualified_name)
        count = 0
        for command in entries:
            if command.qualified_name == "help":
                continue
            if isinstance(command, commands.Group):
                if command.qualified_name == "jishaku":
                    continue
                count += len(command.commands)
            else:
                count += 1
        description = f"""
        [Invite me to your server]({bot.invite_url})
        I'm here to create temporary voice channels and delete them when they are empty.
        **Commands - {count}**
        {default_help.format(prefix=self.context.prefix)}
        Want more help on a command?
        Do `{self.context.prefix}help <Command>`
        """
        embed = discord.Embed(title="Hi there!", description=description, colour=get_colour())
        embed.set_footer(text=f"Requested by {self.context.author}", icon_url=str(self.context.author.avatar_url))
        embed.timestamp = self.context.message.created_at
        await self.context.send(embed=embed)

    def command_formatting(self, embed, command):
        embed.title = command.qualified_name.title()
        desc = ""
        if command.description:
            desc += f"\n\n{command.description}\n\n{command.help}"
        else:
            desc += "\n\n" + (command.help or "No help found...")
        embed.description = desc
        embed.add_field(name="Usage", value="`" + self.context.prefix + self.get_command_signature(command) + "`")
        embed.set_footer(text=f"Requested by {self.context.author}", icon_url=str(self.context.author.avatar_url))
        embed.timestamp = self.context.message.created_at

    async def send_command_help(self, command):
        embed = discord.Embed(colour=get_colour())
        self.command_formatting(embed, command)
        await self.context.send(embed=embed)

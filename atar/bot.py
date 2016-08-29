import sys
import random
import discord
import inspect
import traceback

from textwrap import dedent

from atar.config import Config, ConfigDefaults
from atar.permissions import Permissions, PermissionsDefaults
from atar.utils import loadFile

from . import exceptions

class ATAR(discord.Client):
    def __init__(self, configFile=ConfigDefaults.options_file, permsFile=PermissionsDefaults.permsFile):
        super().__init__()
        
        self.config = Config(configFile)
        self.permissions = Permissions(permsFile, grantAll=[self.config.owner_id])
        
        self.blacklist = set(loadFile(self.config.blacklistFile))
    
    async def cmd_help(self, command=None):
        """
        Usage:
            {commandPrefix}help [command]

        Prints a help message.
        If a command is specified, it prints a help message for that command.
        Otherwise, it lists the available commands.
        """

        if command:
            cmd = getattr(self, 'cmd_' + command, None)
            if cmd:
                return Response(
                    "```\n{}```".format(
                        dedent(cmd.__doc__),
                        commandPrefix=self.config.commandPrefix
                    ),
                    delete_after=60
                )
            else:
                return Response("No command under that name.", delete_after=10)

        else:
            helpmsg = "Commands:\n```"
            commands = []

            for att in dir(self):
                if att.startswith('cmd_') and att != 'cmd_help':
                    command_name = att.replace('cmd_', '').lower()
                    commands.append("{}{}".format(self.config.commandPrefix, command_name))

            helpmsg += ", ".join(commands)
            helpmsg += "```"
            helpmsg += "https://github.com/Dinokaiz2/AT-ARDiscordBot/wiki/Commands"

            return Response(helpmsg, reply=True, delete_after=60)

    async def cmd_roll(self, roll, operator = None, mod = None):
        """
        Usage:
            {commandPrefix}roll [number of dice] "d" dieValue [+ or -] [modifier]

        Rolls dice.
        Can be used with or without spaces around the operator (Ex: 2d20+3/2d20 + 3).
        """
        try:
            *numDice, dieValue = roll.split("d", 1)
            if numDice: numDice = numDice[0]
            if "+" in dieValue or "-" in dieValue:
                # No spaces, unpack
                if "+" in dieValue: operator = "+"
                elif "-" in dieValue: operator = "-"
                dieValue, mod = dieValue.split(operator, 1)
                if not mod and mod != 0: raise ValueError("Operator found, but no modifier.")
            if operator != None and len(operator) > 1: raise ValueError("Operator contained more than '+' or '-'.")
            # numDice, dieValue, operator, mod
            if not mod: mod = 0
            if not numDice: numDice = 1
            numDice, dieValue, mod = [int(x) for x in [numDice, dieValue, mod]]
            msg = ""
            sum = 0
            log = []
            for i in range(1, numDice + 1):
                if operator == "+":
                    log.append(random.randint(1, dieValue) + mod)
                elif operator == "-":
                    log.append(random.randint(1, dieValue) - mod)
                else:
                    log.append(random.randint(1, dieValue))
                sum += log[-1]
            msg += "Result: " + str(sum)
            if numDice == 1:
                if operator == "+" and log[i-1] - mod == 1: msg += " :thumbsdown:"
                elif operator == "+" and log[i-1] - mod == dieValue: msg += " :ok_hand:"
                elif operator == "-" and log[i-1] + mod == 1: msg += " :thumbsdown:"
                elif operator == "-" and log[i-1] + mod == dieValue: msg += " :ok_hand:"
                elif operator != "+" and operator != "-" and log[i-1] == 1: msg += " :thumbsdown:"
                elif operator != "+" and operator != "-" and log[i-1] == dieValue: msg += " :ok_hand:"
            elif 1 < numDice <= 10:
                for i in range(1, numDice + 1):
                    msg += "\nRoll " + str(i) + ": " + str(log[i-1])
                    if operator == "+" and log[i-1] - mod == 1: msg += " :thumbsdown:"
                    elif operator == "+" and log[i-1] - mod == dieValue: msg += " :ok_hand:"
                    elif operator == "-" and log[i-1] + mod == 1: msg += " :thumbsdown:"
                    elif operator == "-" and log[i-1] + mod == dieValue: msg += " :ok_hand:"
                    elif operator != "+" and operator != "-" and log[i-1] == 1: msg += " :thumbsdown:"
                    elif operator != "+" and operator != "-" and log[i-1] == dieValue: msg += " :ok_hand:"
            elif numDice > 10:
                msg += "\nNumber of dice too high to print all rolls."
            elif numDice < 1: raise ValueError("Number of dice must be greater than 0.\nThe number of dice was " + str(numDice) + ".")
            return Response(msg, reply = True)
        except ValueError as v:
            msg = "Invalid roll!"
            if v.args:
                msg += " Reason: ```"
                for arg in v.args:
                    msg += arg
                msg += "```"
            return Response(msg)

    async def cmd_fliptable(self):
        """
        Usage:
            {commandPrefix}fliptable / tableflip

        Flips table.
        """
        return Response("(╯°□°)╯︵ ┻━┻")

    async def cmd_tableflip(self):
        """
        Usage:
            {commandPrefix}tableflip / fliptable

        Flips table.
        """
        return Response("(╯°□°)╯︵ ┻━┻")
        
    async def cmd_shrug(self):
        """
        Usage:
            {commandPrefix}shrug

        Shrugs.
        """
        return Response("¯\_(ツ)_/¯")

    async def cmd_lenny(self):
        """
        Usage:
            {commandPrefix}lenny

        Lenny face.
        """
        return Response("( ͡° ͜ʖ ͡°)")

    async def on_message(self, message):
        await self.wait_until_ready()

        messageContent = message.content.strip()
        if not messageContent.startswith(self.config.commandPrefix):
            return

        if message.author == self.user:
            self.safePrint("Received command from self, ignoring. (%s)" % message.content)
            return

        if self.config.bound_channels and message.channel.id not in self.config.bound_channels and not message.channel.is_private:
            return  # if I want to log this I just move it under the prefix check

        command, *args = messageContent.split()  # Uh, doesn't this break prefixes with spaces in them (it doesn't, config parser already breaks them)
        command = command[len(self.config.commandPrefix):].lower().strip()

        handler = getattr(self, 'cmd_%s' % command, None)
        if not handler:
            return

        if message.channel.is_private:
            if not (message.author.id == self.config.owner_id and command == 'joinserver'):
                await self.send_message(message.channel, "You can't access that command in PMs.")
                return

        if message.author.id in self.blacklist and message.author.id != self.config.owner_id:
            self.safePrint("[User blacklisted] {0.id}/{0.name} ({1})".format(message.author, messageContent))
            return

        else:
            self.safePrint("[Command] {0.id}/{0.name} ({1})".format(message.author, messageContent))

        userPermissions = self.permissions.forUser(message.author)

        argspec = inspect.signature(handler)
        params = argspec.parameters.copy()

        # noinspection PyBroadException
        try:

            handler_kwargs = {}
            if params.pop('message', None):
                handler_kwargs['message'] = message

            if params.pop('channel', None):
                handler_kwargs['channel'] = message.channel

            if params.pop('author', None):
                handler_kwargs['author'] = message.author

            if params.pop('server', None):
                handler_kwargs['server'] = message.server
            
            if params.pop('permissions', None):
                handler_kwargs['permissions'] = userPermissions

            if params.pop('userMentions', None):
                handler_kwargs['userMentions'] = list(map(message.server.get_member, message.raw_mentions))

            if params.pop('channelMentions', None):
                handler_kwargs['channelMentions'] = list(map(message.server.get_channel, message.raw_channel_mentions))

            if params.pop('leftoverArgs', None):
                handler_kwargs['leftoverArgs'] = args

            args_expected = []
            for key, param in list(params.items()):
                doc_key = '[%s=%s]' % (key, param.default) if param.default is not inspect.Parameter.empty else key
                args_expected.append(doc_key)

                if not args and param.default is not inspect.Parameter.empty:
                    params.pop(key)
                    continue

                if args:
                    argValue = args.pop(0)
                    handler_kwargs[key] = argValue
                    params.pop(key)

            if message.author.id != self.config.owner_id:
                if userPermissions.commandWhitelist and command not in userPermissions.commandWhitelist:
                    raise exceptions.PermissionsError(
                        "That command is not enabled for your group (%s)" % userPermissions.name)

                elif userPermissions.commandBlacklist and command in userPermissions.commandBlacklist:
                    raise exceptions.PermissionsError(
                        "That command is disabled for your group (%s)" % userPermissions.name)

            if params:
                docs = getattr(handler, '__doc__', None)
                if not docs:
                    docs = 'Usage: {}{} {}'.format(
                        self.config.commandPrefix,
                        command,
                        ' '.join(args_expected)
                    )

                docs = '\n'.join(l.strip() for l in docs.split('\n'))
                await self.safeSendMessage(
                    message.channel,
                    '```\n%s\n```' % docs.format(commandPrefix=self.config.commandPrefix),
                    expire_in=60
                )
                return

            response = await handler(**handler_kwargs)
            if response and isinstance(response, Response):
                content = response.content
                if response.reply:
                    content = '%s: %s' % (message.author.mention, content)

                sentmsg = await self.safeSendMessage(
                    message.channel, content
                )

        except (exceptions.CommandError, exceptions.HelpfulError) as e:
            print("{0.__class__}: {0.message}".format(e))

            expirein = e.expireIn if self.config.delete_messages else None
            alsodelete = message if self.config.delete_invoking else None

            await self.safeSendMessage(
                message.channel,
                '```\n%s\n```' % e.message,
                expire_in=expirein,
                also_delete=alsodelete
            )

        except exceptions.Signal:
            raise

        except Exception:
            traceback.print_exc()
            if self.config.debug_mode:
                await self.safeSendMessage(message.channel, '```\n%s\n```' % traceback.format_exc())

    def run(self):
        try:
            self.loop.run_until_complete(self.start(*self.config.auth))

        except discord.errors.LoginFailure:
            print("o no")
            raise exceptions.HelpfulError(
                "Can't log in, bad credentials.",
                "Fix email/pass or token in the options file."
                "Each field should be on its own line.")

        finally:
            try:
                self._cleanup()
            except Exception as e:
                print("Encountered error while cleaning:", e)

            self.loop.close()
            if self.exit_signal:
                raise self.exit_signal
    
    async def safeSendMessage(self, dest, content, *, tts=False, expire_in=0, also_delete=None, quiet=False):
        msg = None
        try:
            msg = await self.send_message(dest, content, tts=tts)

        except discord.Forbidden:
            if not quiet:
                self.safe_print("No permission to send message to %s" % dest.name)

        except discord.NotFound:
            if not quiet:
                self.safe_print("Unable to send message to %s" % dest.name)

        return msg

    def safePrint(self, content, *, end='\n', flush=True):
        sys.stdout.buffer.write((content + end).encode('utf-8', 'replace'))
        if flush: sys.stdout.flush()

    async def sendTyping(self, destination):
        try:
            return await super().send_typing(destination)
        except discord.Forbidden:
            if self.config.debug_mode:
                print("Could not send typing to %s, no permission" % destination)


class Response:
    def __init__(self, content, reply=False, delete_after=0):
        self.content = content
        self.reply = reply
        self.delete_after = delete_after

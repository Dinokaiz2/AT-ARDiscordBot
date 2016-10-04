import os
import re
import sys
import time
import random
import asyncio
import discord
import inspect
import traceback
from cleverbot import Cleverbot

from math import *
from textwrap import dedent

from atar.config import Config, ConfigDefaults
from atar.permissions import Permissions, PermissionsDefaults
from atar.utils import loadFile
import atar.fight as fight
import atar.insult as insult
import atar.navyseal as navyseal
import atar.rollhelper as rollhelper

from . import exceptions

class FileHelper:
    @staticmethod
    def get_all_lines_in_block(startLine, lines):
        line_numbers = [startLine]
        for i in range(1, 100):
            line_numbers.append(line_numbers[-1]+1)
            if '}' in lines[line_numbers[-1]]:
                return line_numbers

    @staticmethod
    def get_full_path(rel_path):
        script_dir = os.path.dirname(__file__)
        abs_file_path = os.path.join(script_dir, rel_path)
        return abs_file_path

class ATAR(discord.Client):
    def __init__(self, configFile=ConfigDefaults.options_file, permsFile=PermissionsDefaults.permsFile):
        super().__init__()
        
        self.config = Config(configFile)
        self.permissions = Permissions(permsFile, grantAll=[self.config.owner_id])
        
        self.blacklist = set(loadFile(self.config.blacklistFile))

        self.config_ascii_doc()
        self.config_meme_doc()

        self.cb = Cleverbot()
        self.fight = None
        self.seriousMode = False
    
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
                        dedent(cmd.__doc__).format(commandPrefix=self.config.commandPrefix)
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

    async def cmd_insult(self, leftoverArgs):
        """
        Usage:
            {commandPrefix}insult person

        Inflicts a sick burn upon the sorry soul of your choosing.
        """
        return Response(str(' '.join(leftoverArgs)) + ": " + insult.getRandomInsult())

    async def cmd_eval(self, leftoverArgs):
        """
        Usage:
            {commandPrefix}eval expression

        Evaluates an numerical expression.
        """
        ex = ' '.join(leftoverArgs)
        safe_list = ['math','acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'de\
        grees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log',\
        'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']
        safe_dict = dict([ (k, locals().get(k, None)) for k in safe_list ])
        safe_dict['abs'] = abs
        try:
            return Response(eval(ex, {"__builtins__": None}, safe_dict), reply=True)
        except SyntaxError as s:
            return Response("```Invalid expression!```")

    async def roll(self, author, leftoverArgs, roll, operator=None, mod=None):
        dis = False
        adv = False
        *numDice, dieValue = roll.split("d", 1)
        if not operator: operator = ""
        if not mod: mod = ""
        if "d" in dieValue or "d" in operator or "d" in mod:
            dieValue = dieValue.replace("d", "")
            roll = roll.replace("d", "")
            operator = operator.replace("d", "")
            mod = mod.replace("d", "")
            dis = True
        elif "a" in dieValue or "a" in operator or "a" in mod:
            dieValue = dieValue.replace("a", "")
            roll = roll.replace("a", "")
            operator = operator.replace("a", "")
            mod = mod.replace("a", "")
            adv = True
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
        if adv:
            for i in range(1, numDice + 1):
                if operator == "+":
                    log.append(max(random.randint(1, dieValue) + mod, random.randint(1, dieValue) + mod))
                elif operator == "-":
                    log.append(max(random.randint(1, dieValue) - mod, random.randint(1, dieValue) - mod))
                else:
                    log.append(max(random.randint(1, dieValue), random.randint(1, dieValue)))
                sum += log[-1]
        elif dis:
            for i in range(1, numDice + 1):
                if operator == "+":
                    log.append(min(random.randint(1, dieValue) + mod, random.randint(1, dieValue) + mod))
                elif operator == "-":
                    log.append(min(random.randint(1, dieValue) - mod, random.randint(1, dieValue) - mod))
                else:
                    log.append(min(random.randint(1, dieValue), random.randint(1, dieValue)))
                sum += log[-1]
        else:
            for i in range(1, numDice + 1):
                if operator == "+":
                    log.append(random.randint(1, dieValue) + mod)
                elif operator == "-":
                    log.append(random.randint(1, dieValue) - mod)
                else:
                    log.append(random.randint(1, dieValue))
                sum += log[-1]
        msg += "Result: " + str(sum)
        if dis:
            msg += " :red_circle:"
        elif adv:
            msg += " :large_blue_circle:"
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

    async def cmd_kill(self, author, person):
        responses = [person + " get in noose\n" + person + " got cri\n" + person + " is drop\nnek is snop\nrip"]
        return Response(random.choice(responses))
    
    async def cmd_roll(self, author, leftoverArgs, roll, operator = None, mod = None):
        """
        Usage:
            {commandPrefix}roll [number of dice] "d" dieValue [+ or -] [modifier] [vantage]

        Rolls dice.
        Can be used with or without spaces around the operator (Ex: 2d20+3/2d20 + 3).
        Throw in an a or d at the end to make it a advantage or disadvantage roll, respectively.
        """
        try:
            if roll == "set":
                key = operator
                if key == None:
                    raise ValueError("No key specified!")
                if mod == None:
                    raise ValueError("No value specified!")
                value = str(mod) + ''.join(leftoverArgs)
                try:
                    attempt = await self.roll(author, None, key)
                    try:
                        if attempt.startswith("Invalid") or key == "d":
                            raise ValueError("Key `" + key + "` is invalid.")
                    except AttributeError:
                        pass
                    except ValueError as v:
                        msg = "Invalid entry!"
                        if v.args:
                            msg += " Reason: ```"
                            for arg in v.args:
                                msg += arg
                            msg += "```"
                        return Response(msg)
                except:
                    pass
                try:
                    attempt = await self.roll(author, leftoverArgs, value)
                    if "Invalid" in attempt.content:
                        return attempt
                except Exception as e:
                    msg = "Unable to execute!"
                    if e.args:
                        msg += " Reason: ```"
                        for arg in e.args:
                            msg += arg
                        msg += "```"
                    return Response(msg)
                try:
                    await rollhelper.RollDict.set(author.id, key, value)
                except LookupError as l:
                    msg = "Lookup failed!"
                    if l.args:
                        msg += " Reason: ```"
                        for arg in l.args:
                            msg += arg
                        msg += "```"
                    return Response(msg)
                return Response("Successfully set key `" + str(key) + "` to value `" + str(value) + "`.", reply=True)
        except ValueError as v:
            msg = "Unable to execute!"
            if v.args:
                msg += " Reason: ```"
                for arg in v.args:
                    msg += arg
                msg += "```"
            return Response(msg)
        try:
            value = await rollhelper.RollDict.get(author.id, roll)
            print(value)
            try:
                return await self.roll(author, None, value, None)
            except ValueError as v:
                msg = "Invalid roll!"
                if v.args:
                    msg += " Reason: ```"
                    for arg in v.args:
                        msg += arg
                    msg += "```"
                return Response(msg)
            except TypeError as t:
                msg = "Invalid roll!"
                if t.args:
                    msg += " Reason: ```"
                    for arg in t.args:
                        msg += arg
                    msg += "```"
                return Response(msg)
            except AttributeError as a:
                msg = "Invalid roll!"
                if a.args:
                    msg += " Reason: ```"
                    for arg in a.args:
                        msg += arg
                    msg += "```"
                return Response(msg)
        except LookupError:
            pass
        try:
            return await self.roll(author, leftoverArgs, roll, operator, mod)
        except ValueError as v:
            msg = "Invalid roll!"
            if v.args:
                msg += " Reason: ```"
                for arg in v.args:
                    msg += arg
                msg += "```"
            return Response(msg)
        except TypeError as t:
            msg = "Invalid roll!"
            if t.args:
                msg += " Reason: ```"
                for arg in t.args:
                    msg += arg
                msg += "```"
            return Response(msg)
        except AttributeError as a:
            msg = "Invalid roll!"
            if a.args:
                msg += " Reason: ```"
                for arg in a.args:
                    msg += arg
                msg += "```"
            return Response(msg)

    async def ascii_fliptable(self):
        return Response("(╯°□°)╯︵ ┻━┻")

    async def ascii_tableflip(self):
        return Response("(╯°□°)╯︵ ┻━┻")
        
    async def ascii_shrug(self):
        return Response("¯\_(ツ)_/¯")

    async def ascii_lenny(self):
        return Response("( ͡° ͜ʖ ͡°)")

    async def ascii_sunglasses(self):
        return Response("⊂(▀¯▀⊂)")

    async def ascii_yay(self):
        return Response("╰( ◕ ᗜ ◕ )╯")

    async def ascii_giff(self):
        return Response("༼つ ◕_◕ ༽つ")

    async def ascii_whytho(self):
        return Response("ლ(ಥ Д ಥ )ლ")

    async def ascii_raisedongers(self):
        return Response("ヽ༼ ◉  ͜  ◉༽ﾉ")

    async def ascii_surprised(self):
        return Response("╰། ◉ ◯ ◉ །╯")

    async def ascii_monocle(self):
        return Response("(╭ರ_⊙)")

    async def ascii_run(self):
        return Response("ᕕ( ՞ ᗜ ՞ )ᕗ")

    async def ascii_finger(self):
        return Response(r"""--------------/¯/) 
-------------/¯  / 
-----------/    / 
-----/´¯/'   '/´¯)
---/   /     /     /  |¯\ 
--(     ´    ´      ¯~/'  ') 
---\                  '     / 
-----\                 /
-------\            ( 
---------\          \
""")

    async def ascii_thumbsup(self):
        return Response("────────────────────░███░\n───────────────────░█░░░█░\n──────────────────░█░░░░░█░\n─────────────────░█░░░░░█░\n──────────░░░───░█░░░░░░█░\n─────────░███░──░█░░░░░█░\n───────░██░░░██░█░░░░░█░\n──────░█░░█░░░░██░░░░░█░\n────░██░░█░░░░░░█░░░░█░\n───░█░░░█░░░░░░░██░░░█░\n──░█░░░░█░░░░░░░░█░░░█░\n──░█░░░░░█░░░░░░░░█░░░█░\n──░█░░█░░░█░░░░░░░░█░░█░\n─░█░░░█░░░░██░░░░░░█░░█░\n─░█░░░░█░░░░░██░░░█░░░█░\n─░█░█░░░█░░░░░░███░░░░█░\n░█░░░█░░░██░░░░░█░░░░░█░\n░█░░░░█░░░░█████░░░░░█░\n░█░░░░░█░░░░░░░█░░░░░█░\n░█░█░░░░██░░░░█░░░░░█░\n─░█░█░░░░░████░░░░██░\n─░█░░█░░░░░░░█░░██░█░\n──░█░░██░░░██░░█░░░█░\n───░██░░███░░██░█░░█░\n────░██░░░███░░░█░░░█░\n──────░███░░░░░░█░░░█░\n──────░█░░░░░░░░█░░░█░\n──────░█░░░░░░░░░░░░█░\n──────░█░░░░░░░░░░░░░█░\n──────░█░░░░░░░░░░░░░█░")

    async def cmd_ascii(self, ascii):
        """
        Usage:
            {{commandPrefix}}ascii name

        Returns the requested ASCII.

        {asciis}
        """
        handler = getattr(self, "ascii_%s" % ascii, None)
        if not handler:
            return Response("```Invalid ASCII! Do {commandPrefix}help ascii to get full list.```".format(commandPrefix=self.config.commandPrefix))
        response = await handler()
        
        return(response)

    def config_ascii_doc(self):
        doc = ""
        asciis = []
        for att in dir(self):
            if att.startswith("ascii_"):
                ascii_name = att.replace('ascii_', '').lower()
                asciis.append("{}".format(ascii_name))
        doc += ", ".join(asciis)
        self.cmd_ascii.__func__.__doc__ = self.cmd_ascii.__func__.__doc__.format(asciis = doc)

    async def meme_template(self):
        return Response("http://i.imgur.com/izuep2h.png")

    async def meme_b8(self):
        return Response("http://i.imgur.com/i2RDg1O.gifv")

    async def meme_triggered(self):
        return Response(random.choice(["http://i.imgur.com/h0LjtCP.gif", "http://i.imgur.com/PijcGEU.gif", "http://i.makeagif.com/media/10-12-2015/VguXuo.gif", "http://i0.kym-cdn.com/photos/images/newsfeed/001/034/138/cd0.gif", "http://i.imgur.com/oOF8IXq.gif", "http://tinyurl.com/j778xgz", "http://tinyurl.com/j5ocud4"]))

    async def meme_enabled(self):
        return await self.meme_triggered()

    async def meme_activated(self):
        return await self.meme_triggered()

    async def meme_deanworks(self):
        return Response("http://i.imgur.com/ByoyMiF.png")

    async def meme_memeworks(self):
        return Response("http://i.imgur.com/Oezyjne.png")

    async def meme_steamworks(self):
        return Response("http://i.imgur.com/bVaGfwa.gifv")

    async def meme_feels(self):
        return Response("http://i.imgur.com/w8fIA.gif")

    async def meme_vladmirnat20(self):
        return Response("http://i.imgur.com/aMVHgnE.gifv")

    async def meme_fork(self):
        return Response("https://i.imgur.com/pZ3WfY4.png")

    async def meme_hobbit(self):
        return Response("http://i.imgur.com/xNsfVBy.jpg")

    async def meme_intense(self):
        return Response("http://i.imgur.com/WGL2dWb.gifv")

    async def meme_memegirls(self):
        return Response("http://i.imgur.com/XuZVAZa.png")

    async def meme_prettygood(self):
        return Response("http://i.imgur.com/yuKUizW.jpg")
    
    async def cmd_meme(self, meme):
        """
        Usage:
            {{commandPrefix}}meme name

        Returns the requested meme.

        {memes}
        """
        handler = getattr(self, "meme_%s" % meme, None)
        if not handler:
            return Response("```Invalid meme! Do {commandPrefix}help meme to get full list.```".format(commandPrefix=self.config.commandPrefix))
        response = await handler()
        
        return(response)

    def config_meme_doc(self):
        doc = ""
        memes = []
        for att in dir(self):
            if att.startswith("meme_"):
                meme_name = att.replace('meme_', '').lower()
                memes.append("{}".format(meme_name))
        doc += ", ".join(memes)
        self.cmd_meme.__func__.__doc__ = self.cmd_meme.__func__.__doc__.format(memes = doc)

    async def cmd_cleverbot(self, query):
        """
        Usage:
            {commandPrefix}cleverbot query

        Sends query to cleverbot and returns the message.
        """
        answer = self.cb.ask(query)
        return Response(answer, reply=True)

    async def cmd_navyseal(self, leftoverArgs):
        """
        Usage:
            {commandPrefix}stats replacement

        Returns the Navy Seal copypasta with replacement.
        """
        MAX_MSG_LEN = 1961
        replacement = ' '.join(leftoverArgs)
        msg = navyseal.copypasta(replacement)
        if len(msg) > MAX_MSG_LEN:
            msg = msg[:MAX_MSG_LEN:]
            return Response(msg + "```Trimmed content, result too long.```")
        return Response(msg)

    async def cmd_stats(self, author, server, stat, user=None):
        """
        Usage:
            {commandPrefix}stats stat [mention]

        Returns the stat score for the requested user.
        If no user was specified, it returns the stat of the invoker.
        """
        try:
            if user == None:
                user = author.id
            else:
                for member in server.members:
                    if user == member.mention:
                        user = member.id
                        break
                else:
                    raise LookupError("User " + str(user) + " does not exist.")
            stat_value = await fight.Stats.get_stat(user, stat.upper(), False)
            if int(stat_value) == stat_value: stat_value = int(stat_value)
            return Response(stat.upper() + ": " + str(stat_value), reply=True)
        except LookupError as l:
            if l.args:
                msg = "```"
                for arg in l.args:
                    msg += arg
                msg += "```"
            return Response(msg)

    async def cmd_register(self, author):
        """
        Usage:
            {commandPrefix}register

        Registers the user invoking it into the fight system.
        """
        try:
            msg = await fight.Stats.register(author.id)
            if msg:
                return Response(msg, reply=True)
        except LookupError as l:
            if l.args:
                msg = "```"
                for arg in l.args:
                    msg += arg
                msg += "```"
            return Response(msg)

    async def cmd_fight(self, author):
        """
        Usage:
            {commandPrefix}fight

        Starts a fight.
        """
        if self.fight:
            return Response("```A battle is already in progress! Use {commandPrefix}attack to attack the monster!```".format(commandPrefix=self.config.commandPrefix))
        self.fight = fight.Fight(author)
        await self.fight.start_monster_attacks()
        return Response(self.fight.monster.generate_start_string())

    async def cmd_attack(self, author):
        """
        Usage:
            {commandPrefix}attack

        Attacks the currently active monster.
        A fight must have already been started using {commandPrefix}fight.
        """
        try:
            response, alive = await self.fight.attack(author)
            if not alive:
                self.fight = None
            return Response(response)
        except AttributeError as a:
            print(a)
            return Response("```No fight is currently in progress! Use {commandPrefix}fight to start a fight!```".format(commandPrefix=self.config.commandPrefix))

    async def cmd_shockingtruth(self):
        """
        Usage:
            {commandPrefix}shockingtruth

        Displays the link to the GitHub repository for a terrible fanfiction.
        Don't do it.
        Don't click on it.
        ...
        Please.
        """
        return Response("https://github.com/Dinokaiz2/The-Shocking-Truth")

    async def cmd_trump(self, leftoverArgs):
        trump_file = FileHelper.get_full_path("quotes/trump.txt")
        try:
            if leftoverArgs[0] == "add":
                del leftoverArgs[0]
                if len(leftoverArgs) == 0:
                    return Reponse("```No addition specified!```")
                addition = ' '.join(leftoverArgs)
                with open(trump_file, "a") as trump:
                    trump.write(addition + "\n")
                return Response("Successfully added \"" + addition + "\" to the database.")
        except IndexError:
            pass
        with open(trump_file, "r") as trump:
            lines = trump.readlines()
        return Response(random.choice(lines).strip(), reply=True)

    async def cmd_quote(self, leftoverArgs):
        """
        Usage:
            {commandPrefix}quote

        Returns a random quote.

        Usage:
            {commandPrefix}quote number

        Returns the quote number specified.

        Usage:
            {commandPrefix}quote add quote

        Adds quote to the database of quotes.

        Usage:
            {commandPrefix}quote remove number

        Removes the quote number specified.
        """
        quotes_file = FileHelper.get_full_path("quotes/general.txt")
        try:
            if leftoverArgs[0] == "add":
                del leftoverArgs[0]
                if len(leftoverArgs) == 0:
                    return Reponse("```No addition specified!```")
                addition = ' '.join(leftoverArgs)
                with open(quotes_file, "a") as quotes:
                    quotes.write(addition + "\n")
                return Response("Successfully added \"" + addition + "\" to the database.")
            elif leftoverArgs[0] == "remove":
                del leftoverArgs[0]
                if len(leftoverArgs) == 0:
                    return Response("```No removal specified!```")
                line_to_remove = leftoverArgs[0]
                try:
                    line_to_remove = int(line_to_remove)
                except ValueError:
                    raise ValueError("Could not parse as integer.")
                if line_to_remove < 1:
                    raise ValueError("Number too low. Quotes start at 1.")
                with open(quotes_file, "r") as quotes:
                    lines = quotes.readlines()
                try:
                    quote = lines[line_to_remove - 1]
                    del lines[line_to_remove - 1]
                except IndexError:
                    raise ValueError("Number too high. Current number of quotes is " + str(len(lines)) + ".")
                lines = "".join(lines)
                with open(quotes_file, "w") as quotes:
                    quotes.write(lines)
                return Response("Successfully deleted quote \"" + str(quote.strip()) + "\".")
            elif leftoverArgs[0]:
                line_number = leftoverArgs[0]
                try:
                    line_number = int(line_number)
                    print(line_number)
                except ValueError:
                    raise ValueError("Could not parse as integer.")
                if line_number < 1:
                    raise ValueError("Number too low. Quotes start at 1.")
                with open(quotes_file, "r") as quotes:
                    lines = quotes.readlines()
                try:
                    quote = lines[line_number - 1]
                except IndexError:
                    raise ValueError("Number too high. Current number of quotes is " + str(len(lines)) + ".")
                quote = quote.strip()
                msg = "Quote " + str(line_number) + ": " + str(quote)
                return Response(msg, reply=True)
        except IndexError:
            pass
        except ValueError as v:
            msg = "Invalid number!"
            if v.args:
                msg += " Reason: ```"
                for arg in v.args:
                    msg += arg
                msg += "```"
            return Response(msg)
        with open(quotes_file, "r") as quotes:
            lines = quotes.readlines()
        if len(lines) == 0:
            return Response("```No quotes currently in the database!```")
        quote = random.choice(lines)
        quote_number = lines.index(quote) + 1
        quote = quote.strip()
        msg = "Quote " + str(quote_number) + ": " + str(quote)
        return Response(msg, reply=True)

    async def cmd_beastie(self):
        letters = ["F", "W", "B"]
        random.shuffle(letters)
        msg = letters[0] + "UCKIN " + letters[1] + "EE " + letters[2] + "EASTIE"
        return Response(msg, reply=True)

    async def cmd_seriousmode(self):
        self.seriousMode = not self.seriousMode
        if not self.seriousMode:
            return Response("Turned serious mode off.", reply=True)
        else:
            return Response("Turned serious mode on.", reply=True)

    async def cleverbot_repeating(self, query, channel):
        time.sleep(0.5)
        answer = self.cb.ask(query)
        await self.safeSendMessage(channel, answer)
        await self.cleverbot_repeating(answer, channel)

    async def on_message(self, message):
        await self.wait_until_ready()
        messageContent = message.content.strip()

        if message.content.startswith("!cleverbot"):
            await self.cleverbot_repeating(message.content.replace("!cleverbot ", ""), message.channel)
            return
        
        if not messageContent.startswith(self.config.commandPrefix):
            if message.author != self.user:
                if ("wow" in message.content.lower() or "mom" in message.content.lower()) and not self.seriousMode:
                    lst, indices = self.split(message.content)
                    for i in indices:
                        if lst[i][0].lower() == "w":
                            lst[i] = self.case_sensitive_replace(lst[i], "wow", "mom")
                        elif lst[i][0].lower() == "m":
                            lst[i] = self.case_sensitive_replace(lst[i], "mom", "wow")
                    await self.safeSendMessage(message.channel, ''.join(lst))
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
##                docs = getattr(handler, '__doc__', None)
##                if not docs:
##                    docs = 'Usage: {}{} {}'.format(
##                        self.config.commandPrefix,
##                        command,
##                        ' '.join(args_expected)
##                    )
##
##                docs = '\n'.join(l.strip() for l in docs.split('\n'))
##                await self.safeSendMessage(
##                    message.channel,
##                    '```\n%s\n```' % docs.format(commandPrefix=self.config.commandPrefix),
##                    expire_in=60
##                )
                response = await self.cmd_help(command)
                await self.safeSendMessage(message.channel,
                                           response.content
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

    def case_sensitive_replace(self, string, old, new):
        """
        replace occurrences of old with new, within string
            replacements will match the case of the text it replaces
        """
        def repl(match):
            current = match.group()
            result = ''
            all_upper=True
            for i,c in enumerate(current):
                if i >= len(new):
                    break
                if c.isupper():
                    result += new[i].upper()
                else:
                    result += new[i].lower()
                    all_upper=False
            #append any remaining characters from new
            if all_upper:
                result += new[i+1:].upper()
            else:
                result += new[i+1:].lower()
            return result

        regex = re.compile(re.escape(old), re.I)
        return regex.sub(repl, string)

    def split(self, str):
        indexes = list(self.find_all(str.lower(), "wow")) + list(self.find_all(str.lower(), "mom"))
        indexes.sort()
        char = 0
        newlist = []
        newlistindices = []
        if indexes[0] != 0:
            newlist.append(str[0:indexes[0]])
        for i in range(0, len(indexes)-1):
            newlist.append(str[indexes[i]:indexes[i]+3])
            newlistindices.append(len(newlist)-1)
            newlist.append(str[indexes[i]+3:indexes[i+1]])
        newlist.append(str[indexes[-1]:indexes[-1]+3])
        newlistindices.append(len(newlist)-1)
        newlist.append(str[indexes[-1]+3:len(str)])
        for i in newlist:
            if i == "":
                newlist.remove(i)
        return newlist, newlistindices

    def find_all(self, a_str, sub):
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1: return
            yield start
            start += len(sub) # use start += 1 to find overlapping matches


class Response:
    def __init__(self, content, reply=False, delete_after=0):
        self.content = content
        self.reply = reply
        self.delete_after = delete_after

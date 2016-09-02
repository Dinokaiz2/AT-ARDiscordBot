import os
import abc
import time
import random
import asyncio
from discord import User as discord_User

class Fight:
    def __init__(self, instigator):
        self.players = [[instigator.id, 0]]

    def add_player(member):
        for player, lastHit in self.players:
            if player == member:
                break
        else:
            # If player not found, add player
            self.players.append([member.id, 0])
            return
        raise ValueError("That player already is already in the battle.")

    def is_in_battle(member):
        for player, lasthit in self.players:
            if player == member:
                return True
        return False

class Monster:
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        self.HP = 0
        self.ATK = 0
        self.DEF = 0
        self.ACC = 0
        self.alive = True
        self.challenge_rating = 0

    async def attack(self, fight, member):
        dmg = self.ATK
        rng = random.randint(int(-dmg * 0.2), int(dmg * 0.2)))
        dmg += rng
        Stats.set_stat(member.id, Stats.HP, dmg, True)

    async def take_damage(damage, ignore_def=False):
        if not ignore_def:
            rng = random.randint(int(-self.DEF * 0.2), int(self.DEF * 0.2))
            reduction = self.DEF + rng
            damage -= reduction
        self.HP -= damage
        if self.HP <= 0: self.alive = False
        else: self.alive = True
        return self.alive

    

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

class Stats:
    statFileDir = FileHelper.get_full_path("stats/ATARStats.txt")
    HP = "HP"
    ATK = "ATK"
    DEF = "DEF"
    ACC = "ACC"
    hp_default = 10
    atk_default = 3
    def_default = 3
    acc_default = 0.9
    stats = [HP, ATK, DEF, ACC]
    statDefaults = {HP: hp_default, ATK: atk_default, DEF: def_default, ACC: acc_default}

    @staticmethod
    async def set_stat(id, stat_type, value, relative=False):
        with open(Stats.statFileDir, "r") as statSheet:
            lines = statSheet.readlines()
        line_numbers = []
        for line in lines:
            if str(id) in line:
                # Don't forget that line_numbers is 0-based
                line_numbers = FileHelper.get_all_lines_in_block(lines.index(line), lines)
                break
        else:
            with open(Stats.statFileDir, "a") as statSheet:
                statSheet.write("\n\n")
                statSheet.write(str(id) + " {\n")
                for stat in Stats.stats:
                    statSheet.write("\t" + stat + ": " + str(Stats.statDefaults.get(stat) + "\n")
                statSheet.write("}")
            await Stats.set_stat(id, stat_type, value, relative)
            return
        for i in line_numbers:
            if stat_type in lines[i]:
                line_number = i
                break
        else:
            lines.insert(line_numbers[-2], "\t" + stat_type + ": " + str(value) + "\n")
            return
        if relative:
            stat = int(lines[line_number].strip().split(": ", 1)[1]) + value
            lines[line_number] = "\t" + stat_type + ": " + str(stat) + "\n"
        else:
            lines[line_number] = "\t" + stat_type + ": " + str(value) + "\n"
        lines = "".join(lines)
        with open(Stats.statFileDir, "w") as statSheet:
            statSheet.write(lines)
    
    @staticmethod
    async def get_stat(id, stat_type, force=True):
        with open(Stats.statFileDir, "r") as statSheet:
            lines = statSheet.readlines()
        line_numbers = []
        for line in lines:
            if str(id) in line:
                # Don't forget that line_numbers is 0-based
                line_numbers = FileHelper.get_all_lines_in_block(lines.index(line), lines)
                break
        else:
            if not force:
                raise LookupError("Stats not found for that ID.")
            with open(Stats.statFileDir, "a") as statSheet:
                statSheet.write("\n\n")
                statSheet.write(str(id) + " {\n")
                for stat in Stats.stats:
                    statSheet.write("\t" + stat + ": " + str(Stats.statDefaults.get(stat) + "\n")
                statSheet.write("}")
            return Stats.get_stat(id, stat_type)
        for i in line_numbers:
            if stat_type in lines[i]:
                line_number = i
                break
        else:
            if not force:
                raise LookupError("Stat " + stat + " not found for that user.")
            lines.insert(line_numbers[-2], "\t" + stat_type + ": " + Stats.statDefaults.get(stat_type) + "\n")
            stat = await get_stat(id, stat_type)
            return stat
        stat = lines[line_number].strip().split(": ", 1)[1]
        return stat

    @staticmethod
    async def register(id):
        with open(Stats.statFileDir, "r") as statSheet:
            lines = statSheet.readlines()
        line_numbers = []
        for line in lines:
            if str(id) in line:
                # Don't forget that line_numbers is 0-based
                line_numbers = FileHelper.get_all_lines_in_block(lines.index(line), lines)
                break
        else:
            with open(Stats.statFileDir, "a") as statSheet:
                statSheet.write("\n\n")
                statSheet.write(str(id) + " {\n")
                for stat in Stats.stats:
                    statSheet.write("\t" + stat + ": " + str(Stats.statDefaults.get(stat) + "\n")
                statSheet.write("}")
            return "Successfully registered!"
        raise LookupError("That user is already registered.")

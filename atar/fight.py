import os
import abc
import time
import random
import asyncio
from discord import User as discord_User

class Fight:
    def __init__(self, instigator):
        self.players = [[instigator.id, 0]]
        self.monster = random.choice([Zombie()]) # Matchmaking
        self.PLAYER_ATTACK_COOLDOWN = 60

    def add_player(self, member, lasthit=0):
        for player, lastHit in self.players:
            if player == member:
                break
        else:
            # If player not found, add player
            self.players.append([member.id, lasthit])
            return
        raise ValueError("That player already is already in the battle.")

    def is_in_battle(self, member):
        for player, lasthit in self.players:
            if player == member:
                return True
        return False

    def get_player_lasthit(self, player, force=False):
        for id, last_hit in self.players:
            if id == player.id:
                return last_hit
        if not force:
            raise ValueError("Player not found!")
        add_player(player, 0)
        return 0

    def set_player_lasthit(self, player, lasthit, force=False):
        i = 0
        for id, last_hit in self.players:
            if id == player.id:
                self.players[i][1] = lasthit
                break
            i += 1
        else:
            if not force:
                raise ValueError("Player not found!")
            add_player(player, lasthit)

    async def attack(self, attacker, force=False):
        if time.time() - self.get_player_lasthit(attacker, force=True) < self.PLAYER_ATTACK_COOLDOWN:
            return "You can\'t fight yet! Check back again in {seconds} seconds.".format(seconds=int(60-(time.time()-self.get_player_lasthit(attacker)))), self.monster.alive
        self.set_player_lasthit(attacker, time.time())
        if random.random() > await Stats.get_stat(attacker.id, Stats.ACC):
            return self.monster.generate_dodge_string().format(player_name=attacker.mention), self.monster.alive
        dmg = await Stats.get_stat(attacker.id, Stats.ATK)
        rng = random.randint(int(-dmg * 0.2), int(dmg * 0.2))
        dmg += rng
        dmg, string = await self.monster.take_damage(int(dmg))
        string = string.format(player_name=attacker.mention, damage=dmg)
        return string, self.monster.alive

class Monster:
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, HP, ATK, DEF, ACC, challenge_rating):
        self.HP = HP
        self.ATK = ATK
        self.DEF = DEF
        self.ACC = ACC
        self.challenge_rating = challenge_rating
        self.alive = True

    async def attack(self, fight, member):
        if random.random() > self.ACC:
            return False, 0, generate_miss_string()
        dmg = self.ATK
        rng = random.randint(int(-dmg * 0.2), int(dmg * 0.2))
        dmg += rng
        Stats.set_stat(member.id, Stats.HP, dmg, True)
        return True, dmg, generate_attack_string()

    async def take_damage(self, damage, ignore_def=False):
        if not ignore_def:
            rng = random.randint(int(-self.DEF * 0.2), int(self.DEF * 0.2))
            reduction = self.DEF + rng
            damage -= reduction
        self.HP -= damage
        if self.HP <= 0:
            self.alive = False
            return damage, "\n".join([self.generate_attack_string(), self.generate_death_string()])
        self.alive = True
        return damage, self.generate_hurt_string()

    @abc.abstractmethod
    def generate_start_string(self):
        """
        Generates a string for when this monster first appears in battle.
        """
        return

    @abc.abstractmethod
    def generate_miss_string(self):
        """
        Generates a string for when the monster misses an attack.
        All strings must contain a player name.
        """
        return

    @abc.abstractmethod
    def generate_dodge_string(self):
        """
        Generates a string for when a player misses an attack on the monster.
        All strings must contain a player name.
        """
        return

    @abc.abstractmethod
    def generate_attack_string(self):
        """
        Generates a string for when the monster hits an attack.
        All strings must contain a player name and a damage dealt value.
        """
        return

    @abc.abstractmethod
    def generate_hurt_string(self):
        """
        Generates a string for when the monster is hit by an attack.
        All strings must contain a player name and a damage taken value.
        """
        return

    @abc.abstractmethod
    def generate_death_string(self):
        """
        Generates a string for when the monster dies.
        """
        return

class Zombie(Monster):
    def __init__(self):
        super().__init__(10, 3, 1, 0.7, 1)

    def generate_start_string(self):
        return random.choice([("A zombie appeared!")])

    def generate_miss_string(self):
        return random.choice([("The zombie lunges at {player_name}!\n"
                              "The attack missed.")])

    def generate_dodge_string(self):
        return random.choice([("{player_name} shot at the zombie with a crossbow!\n"
                              "The attack missed.")])

    def generate_attack_string(self):
        return random.choice([("The zombie lunges at {player_name}!\n"
                               "{player_name} was bit by the zombie.\n"
                               "They took {damage} damage.")])

    def generate_hurt_string(self):
        return random.choice([("{player_name} shot at the zombie with a crossbow!\n"
                               "The bolt hits the zombie. It loses {damage} health.")])

    def generate_death_string(self):
        return random.choice([("The zombie falls to the ground and dies.")])

    

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
                    statSheet.write("\t" + stat + ": " + str(Stats.statDefaults.get(stat)) + "\n")
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
                    statSheet.write("\t" + stat + ": " + str(Stats.statDefaults.get(stat)) + "\n")
                statSheet.write("}")
            return await Stats.get_stat(id, stat_type)
        for i in line_numbers:
            if stat_type in lines[i]:
                line_number = i
                break
        else:
            if not force:
                raise LookupError("Stat " + stat_type + " not found for that user.")
            lines.insert(line_numbers[-2], "\t" + stat_type + ": " + str(Stats.statDefaults.get(stat_type)) + "\n")
            with open(Stats.statFileDir, "w") as statSheet:
                statSheet.write("".join(lines))
            stat = await Stats.get_stat(id, stat_type)
            return float(stat)
        stat = lines[line_number].strip().split(": ", 1)[1]
        return float(stat)

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
                    statSheet.write("\t" + stat + ": " + str(Stats.statDefaults.get(stat)) + "\n")
                statSheet.write("}")
            return "Successfully registered!"
        raise LookupError("That user is already registered.")

import asyncio
import os

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

class RollDict:
    roll_dict_dir = FileHelper.get_full_path("rolldata\RollDict.txt")
    
    @staticmethod
    async def set(id, key, value):
        with open(RollDict.roll_dict_dir, "r") as rollDict:
            lines = rollDict.readlines()
        line_numbers = []
        for line in lines:
            if str(id) in line:
                # Don't forget that line_numbers is 0-based
                line_numbers = FileHelper.get_all_lines_in_block(lines.index(line), lines)
                break
        else:
            with open(RollDict.roll_dict_dir, "a") as rollDict:
                rollDict.write("\n\n")
                rollDict.write(str(id) + " {\n")
                rollDict.write("\t" + str(key) + ": " + str(value) + "\n")
                rollDict.write("}")
            return
        for i in line_numbers:
            if key in lines[i]:
                line_number = i
                lines[line_number] = "\t" + str(key) + ": " + str(value) + "\n"
                break
        else:
            lines.insert(line_numbers[-2], "\t" + str(key) + ": " + str(value) + "\n")
        lines = "".join(lines)
        with open(RollDict.roll_dict_dir, "w") as rollDict:
            rollDict.write(lines)

    @staticmethod
    async def get(id, key):
        with open(RollDict.roll_dict_dir, "r") as rollDict:
            lines = rollDict.readlines()
        line_numbers = []
        for line in lines:
            if str(id) in line:
                # Don't forget that line_numbers is 0-based
                line_numbers = FileHelper.get_all_lines_in_block(lines.index(line), lines)
                break
        else:
            raise LookupError("Your ID could not be found in the system.")
        for i in line_numbers:
            try:
                if key in lines[i].split(":")[0]:
                    line_number = i
                    break
            except:
                pass
        else:
            try:
                raise LookupError("Key `" + key + "` not found for that ID.")
            except TypeError as t:
                raise LookupError("No key found!")
        value = lines[line_number].strip().split(": ", 1)[1]
        return value

    @staticmethod
    async def remove(id, key):
        with open(RollDict.roll_dict_dir, "r") as rollDict:
            lines = rollDict.readlines()
        line_numbers = []
        for line in lines:
            if str(id) in line:
                # Don't forget that line_numbers is 0-based
                line_numbers = FileHelper.get_all_lines_in_block(lines.index(line), lines)
                break
        else:
            raise LookupError("Your ID could not be found in the system.")
        for i in line_numbers:
            if key in lines[i]:
                line_number = i
                break
        else:
            raise LookupError("The specified key could not be found under your ID.")
        del lines[line_number]
        lines = "".join(lines)
        with open(RollDict.roll_dict_dir, "w") as rollDict:
            rollDict.write(lines)

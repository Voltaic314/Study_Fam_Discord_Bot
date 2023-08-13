"""
Author: Logan Maupin

The purpose of this python script is to house the text processing class which houses a bunch of methods for manipulating
strings and text files.
"""
import random


class Text_Processing:

    @staticmethod
    def list_of_lines_in_text_file(filename: str) -> list[str]:

        lines_of_file = []

        with open(filename, "r") as file:
            for line in file:
                # This if statement is to prevent this from adding empty line strings to the list.
                if line:
                    lines_of_file.append(line.strip())

        return lines_of_file

    @staticmethod
    def get_random_string_from_list(list_of_strings: list[str]) -> str:
        return random.choice(list_of_strings)

    @staticmethod
    def get_random_line_from_text_file(filename: str) -> str:
        lines = Text_Processing.list_of_lines_in_text_file(filename)
        return Text_Processing.get_random_string_from_list(lines)
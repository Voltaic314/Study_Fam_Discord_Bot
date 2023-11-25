import time
from datetime import datetime
import math


class Time_Stuff:

    @staticmethod
    def get_current_time_in_epochs() -> float:
        return time.time()

    @staticmethod
    def convert_epochs_to_human_readable_time(epochs: float) -> str:
        return time.ctime(float(math.floor(epochs)))

    @staticmethod
    def get_current_date() -> str:
        return datetime.now().strftime('%m/%d/%y')
    
    @staticmethod
    def convert_date_time_string_to_strp_object(date: str, time: str):
        return datetime.strptime(f'{date} {time}', "%d-%m-%Y %H:%M")

    @staticmethod
    def how_many_minutes_apart(epoch_time_one: float, epoch_time_two: float) -> list[float]:
        """
        This function takes 2 times in epoch seconds that are floats and returns a list with 3 integers provided in the
        format of minutes, hours, days in ascending order. This can be used for reference when the user wants to check
        how much time they have left in focus mode.
        :param epoch_time_one: float that represents the time in epochs
        :param epoch_time_two: float #2 that also represents the time in epochs.
        :returns: list of floats of how much time is left in a human-readable format. ex: [minutes, hours, days]
        """
        time_diff = abs(epoch_time_one - epoch_time_two)
        minutes = (time_diff // 60) % 60
        hours = (time_diff // 3600) % 24
        days = time_diff // 86400
        return [minutes, hours, days]


    @staticmethod
    def check_user_formatting_for_long_term_remiinders(date: str, time: str) -> str:
        # formatting user_input strings to remove any extra spaces
        date = date.strip()
        time = time.strip()

        redacted_date_str: str = ''

        for character in date:
            if character == '-':
                redacted_date_str += character
            elif character.isdigit():
                redacted_date_str += 'x'
        
        if redacted_date_str != 'xx-xx-xxxx':
            return "incorrect date format"
        

        redacted_time_str: str = ''

        for character in time:
            if character == ':':
                redacted_time_str += character
            elif character.isdigit():
                redacted_time_str += 'x'

        if redacted_time_str != 'xx:xx' or len(time) != 5:
            return "incorrect time format"
        
        return "correct format"

    @staticmethod
    def time_responses_for_focus(minutes: int) -> str:

        #  If the user requested to be in focus for longer than a week or less than 0 minutes, call them a moron. lol
        if minutes > 10080 or minutes < 0:
            return "Please input a number of minutes that is between 1 and 1440."

        if minutes == 1:
            return f"You will now be in focus mode for {minutes} minute."

        if 1 < minutes < 60:
            return f"You will now be in focus mode for {minutes} minutes."

        if minutes == 60:
            hours = int(minutes / 60)
            return f"You will now be in focus mode for {hours} hour."

        if minutes > 60 and minutes % 60 == 0:
            hours = int(minutes / 60)
            return f"You will now be in focus mode for {hours} hours."

        if minutes > 60 and minutes % 60 != 0:
            hours = int(minutes / 60)
            minutes_after_hour_division = minutes % 60
            return f"You will now be in focus mode for {hours} hours and {minutes_after_hour_division} minutes."

        if minutes == 1440:
            return "You will now be in focus mode for 1 day."

        if minutes > 1440 and minutes % 1440 == 0:
            days = int(minutes / 1440)
            hours = int((minutes % 1440) / 60)
            minutes_after_hour_division = hours % 60
            return f"You will now be in focus mode for {days} days, {hours} hours, and {minutes_after_hour_division}" \
                   f" minutes."

        else:
            return "Please input a number of minutes that is between 1 and 1440"

    @staticmethod
    def is_input_time_past_threshold(input_time_in_epochs: float, threshold_time_in_seconds: int,
                                     discord_time: bool) -> bool:
        """
        Takes an input time in epoch seconds and determines if this time is over 24 hours old.
        :param input_time_in_epochs: an input time that is specifically in epoch seconds. like time.time()
        :param threshold_time_in_seconds: an input time integer of seconds needed to say whether the input time is past
        that point or not. I.e. for example 86400 would say is the input time older than 24 hours ago.
        :param discord_time: This is a flag that needs to be set to true if passing in a discord message since discord
        message timestamps are returned in UTC time. Otherwise, it throws off the calculations.
        :returns: True if the time is over 24 hours old, false otherwise.
        """
        current_time = time.time()
        if not input_time_in_epochs:
            return False
        
        if discord_time:
            utc_offset_for_dst = 3600 * 5
            utc_offset_for_non_dst = 3600 * 6
            actual_message_time_in_EST = input_time_in_epochs - utc_offset_for_dst
            time_difference_of_current_vs_input = current_time - actual_message_time_in_EST
            return time_difference_of_current_vs_input >= threshold_time_in_seconds

        else:
            time_difference_of_current_vs_input = current_time - input_time_in_epochs
            return time_difference_of_current_vs_input >= threshold_time_in_seconds

    @staticmethod
    def next_occurrence_epoch(target_hour):
        # Get the current time in epoch seconds
        current_time = time.time()

        # Get the current date in struct_time format
        current_date = time.localtime(current_time)

        # Calculate the next occurrence date by updating the hour
        next_occurrence_date = time.struct_time((
            current_date.tm_year,
            current_date.tm_mon,
            current_date.tm_mday,
            target_hour,
            0,  # Set minutes to 0
            0,  # Set seconds to 0
            current_date.tm_wday,
            current_date.tm_yday,
            current_date.tm_isdst
        ))

        # Convert the next occurrence date to epoch seconds
        next_occurrence_epoch = time.mktime(next_occurrence_date)

        # If the next occurrence is before the current time, add a day
        if next_occurrence_epoch <= current_time:
            next_occurrence_epoch += 24 * 60 * 60  # Add 1 day in seconds

        return next_occurrence_epoch

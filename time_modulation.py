import time
import math


class Time_Stuff:

    @staticmethod
    def get_current_time_in_epochs() -> float:
        return time.time()

    @staticmethod
    def convert_epochs_to_human_readable_time(epochs: float) -> str:
        return time.ctime(float(math.floor(epochs)))

    @staticmethod
    def add_time(current_epoch: float, minutes_to_add: int) -> float:
        seconds_to_add: float = float(minutes_to_add * 60)
        return current_epoch + seconds_to_add

    @staticmethod
    def how_many_minutes_apart(epoch_time_one: float, epoch_time_two: float) -> list[int]:
        """
        This function takes 2 times in epoch seconds that are floats and returns a list with 3 integers provided in the
        format of minutes, hours, days in ascending order. This can be used for reference when the user wants to check
        how much time they have left in focus mode.
        :param epoch_time_one: float that represents the time in epochs
        :param epoch_time_two: float #2 that also represents the time in epochs.
        :returns: list of integers of how much time is left in a human-readable format. ex: [minutes, hours, days]
        """
        time_diff = abs(epoch_time_one - epoch_time_two)
        minutes = (time_diff // 60) % 60
        hours = (time_diff // 3600) % 24
        days = time_diff // 86400
        return [minutes, hours, days]

    @staticmethod
    def time_responses(minutes: int) -> str:

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

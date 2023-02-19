import time


class Time_Stuff:

    @staticmethod
    def get_current_time_in_epochs() -> float:
        return time.time()

    @staticmethod
    def convert_epochs_to_human_readable_time(epochs: float) -> str:
        return time.ctime(epochs)

    @staticmethod
    def add_time(current_epoch: float, minutes_to_add: int):
        seconds_to_add: float = float(minutes_to_add * 60)
        return current_epoch + seconds_to_add

    @staticmethod
    def how_many_minutes_apart(epoch_time_one: float, epoch_time_two: float) -> int:
        time_difference = float(epoch_time_two) - float(epoch_time_one)
        return (time_difference // 60) * -1

    @staticmethod
    def time_responses(minutes: int):

        if minutes > 1440 or minutes < 0:
            return "Please input a number of minutes that is between 1 and 1440"

        if minutes == 1:
            return f"You will now be in focus mode for {minutes} minute!"

        if 1 < minutes < 60:
            return f"You will now be in focus mode for {minutes} minutes!"

        if minutes == 60:
            hours = minutes / 60
            return f"You will now be in focus mode for {hours} hour!"

        if minutes > 60 and minutes % 60 == 0:
            hours = minutes // 60
            return f"You will now be in focus mode for {hours} hours!"

        if minutes > 60 and minutes % 60 != 0:
            hours = minutes // 60
            minutes_after_hour_division = minutes % 60
            return f"You will now be in focus mode for {hours} hours and {minutes_after_hour_division} minutes!"

        if minutes == 1440:
            return "You will now be in focus mode for 1 day."

        else:
            return "Please input a number of minutes that is between 1 and 1440"

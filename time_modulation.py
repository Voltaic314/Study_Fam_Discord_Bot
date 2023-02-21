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
        time_difference = float(epoch_time_one) - float(epoch_time_two)
        return int(time_difference / 60)

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

    @staticmethod
    def pomodoro_session_length(study_interval: int, short_break: int, long_break: int, amount_of_pomos: int) -> int:
        return ((study_interval * 3) + (short_break * 3) + long_break) * amount_of_pomos

    @staticmethod
    def pomo_responses_initial(pomo_sessions, break_time_amount: int, next_break_in_x_minutes,
                               end_time: int):
        if pomo_sessions <= 0:
            return "You must enter a number of sessions that are greater or equal to 1"

        elif pomo_sessions >= 1:
            return f"Your pomodoro has started. Your next break will be {break_time_amount} minutes starting in " \
                   f"{next_break_in_x_minutes} minutes. Your pomodoro will end in {end_time} minutes"

    @staticmethod
    def completed_pomodoro(current_pomo_interval: int) -> str:
        if current_pomo_interval == 2:
            return "You have completed a Pomodoro!"
        elif current_pomo_interval > 2 and current_pomo_interval % 2 == 0:
            total_pomodoros_completed = current_pomo_interval / 2
            return f"You have completed {total_pomodoros_completed} pomodoros!"

    @staticmethod
    def next_break_time_pomo_default(interval: int) -> int:

        pomo_times = [5, 5, 5, 20]
        index_for_pomo_times = (interval % 4)
        return pomo_times[index_for_pomo_times]

    @staticmethod
    def we_should_be_on_pomo_break(interval: int) -> bool:
        pomo_interval = interval % 8
        if pomo_interval % 2 == 0:
            return True
        else:
            return False


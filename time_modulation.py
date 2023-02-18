import time


class Time_Stuff:

    @property
    def get_current_time_in_epochs(self) -> float:
        return time.time()

    @staticmethod
    def convert_epochs_to_human_readable_time(epochs: float) -> str:
        return time.ctime(epochs)

    @staticmethod
    def add_time(current_epoch: float, minutes_to_add: int):
        seconds_to_add: float = float(minutes_to_add * 60)
        return current_epoch + seconds_to_add

    def how_many_minutes_apart(self, epoch_time_one: float, epoch_time_two: float) -> float:
        time_difference = epoch_time_two - epoch_time_one
        return time_difference

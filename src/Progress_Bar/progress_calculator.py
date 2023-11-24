'''
Author: Logan Maupin

The purpose of this module is primarily to do the actual
calculation of the yearly progress we have made through 
these hellacious years of our lives. 
'''
import time
import calendar

def is_leap_year() -> bool:
    '''
    This function determines whether or not the current year is a leap year.

    Returns: bool - True if the current year is a leap year.
    '''
    year = time.localtime()[0]
    return calendar.isleap(year)


def build_year_dict() -> dict[int, int]:
    '''
    This function builds a dictionary where the keys
    are the calendar number month (like "1" for January) 
    and the values are the integers of how many days 
    they have respectively.

    Parameters:
    leap_year: boolean value of whether the current year is a leap year.

    Returns: dictionary object with str keys and int values
    '''
    yearly_dict = {
        1: 31,
        2: 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31, 
        11: 30,
        12: 31,
    }

    leap_year = is_leap_year()
    if leap_year:
        yearly_dict["February"] = 29

    return yearly_dict


def get_current_month_and_day() -> int:
    '''
    This function just returns whatever the current month is.

    Returns: str - name of the current month like "January".
    '''
    return time.localtime()[1], time.localtime()[2]


def calculate_current_day_number(month_int: int, day_int: int) -> int:
    '''
    This function takes 2 arguments, the current calendar number month
    and number day it is. like 11 as the month int and 23 as the day int
    would mean the current date is 11/23 (or 23/11 depending on your format).

    It then returns what day that is overall in the year like the 276th day for example.

    Parameters:
    month_int: int - number representing the current month from 1 to 12
    day_int: int - number representing the current day from 1 to 31 or 
    whatever the max day int could be for that month (this is checked).

    Returns: int - current int day of the year. like 276. 
    '''
    calendar_dict = build_year_dict()

    # make sure the user gave us a valid month int
    if month_int not in calendar_dict:
        print("Please use a number for the month that is between 1 and 12 inclusive...")
        raise ValueError
    
    # if they gave us a valid month int, make sure the day int is also valid.
    max_possible_day = calendar_dict[month_int]    
    if not (1 <= day_int <= max_possible_day):
        print("Please use a valid number value for the day of the month.")
        raise ValueError
    
    # if the above conditions didn't raise an error, let's continue on.
    day_sum = day_int
    for i in range(1, month_int):
        day_sum += calendar_dict[i]

    return day_sum


def calculate_yearly_progress_decimal(total_day_int: int, leap_year: bool) -> float:
    '''
    This function takes an argument of the total day number it is 
    of the year, divides it by 365 (or 366 if it's a leap year),
    then returns that rounded to 4 decimal places. :) 

    Parameters: 
    total_day_int: int - like 276, if it was the 276th day of the year. 
    This can be calculated using the calculate_current_day_number function.
    leap_year: bool - True if the current year is a leap year, false otherwise.

    Returns: float - like 0.6678 meaning we are 66.78% of the way through the year.
    '''
    if leap_year:
        return round(total_day_int / 366, 4)
    else:
        return round(total_day_int / 365, 4)
    

def format_progress_bar_string(total_day_float: float) -> str:
    '''
    This function takes the percentage floats, mutliplies it by 100,
    then puts it into a formatted string for you to use in img captions.

    Parameters:
    total_day_float: percentage of how far we are through the year in decimal form

    Returns: str - like "66.78%" indicating we are 66.78% of the way through the year.
    '''
    # did an extra round for redundancy sake
    return f'{round(total_day_float * 100, 2)}%'


def get_total_yearly_percentage() -> float:
    '''
    This function is basically just an example function that defines
    the order in which you could call these functions to get the decimal 
    value of the yearly progress percentage

    Returns: float - percentage from 0 to 1 of the current yearly progress.
    '''
    leap_year = is_leap_year()
    month, day = get_current_month_and_day()
    total_day_number = calculate_current_day_number(month, day)
    yearly_progress_decimal = calculate_yearly_progress_decimal(total_day_number, leap_year)
    return yearly_progress_decimal


if __name__ == "__main__":
    print(format_progress_bar_string(get_total_yearly_percentage()))

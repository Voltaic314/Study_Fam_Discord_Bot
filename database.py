import sqlite3
import os


class Database:

    def __init__(self, file_path_and_name: str):
        self.file_path_and_name = file_path_and_name
        self.connect = sqlite3.connect(file_path_and_name)
        self.cursor = self.connect.cursor()

    def table_column_names(self, table_name: str):
        # retrieve the column names for the specified table
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return self.cursor.fetchall()

    def log_to_DB(self, formatted_tuple: tuple, table_to_add_values_to: str):
        """
        The purpose of this function is to log our grabbed info from the get_photo function over to the database
        :param formatted_tuple: tuple containing the info that the user wishes to log to the database.
        :param table_to_add_values_to: The name of the table in the database that you want to append an entry to.
        :returns: None
        """

        # The if is to make sure there is anything in the tuple at all, otherwise don't log anything to the database.
        if formatted_tuple:
            if len(formatted_tuple) > 1:
                formatted_string = "("
                formatted_string += "?, " * (len(formatted_tuple) - 1)
                formatted_string += "?)"
                self.cursor.execute(f'INSERT INTO {table_to_add_values_to} VALUES {formatted_string}', formatted_tuple)
                self.connect.commit()

            elif len(formatted_tuple) == 1:
                formatted_string = "(?)"
                self.cursor.execute(f'INSERT INTO {table_to_add_values_to} VALUES {formatted_string}', formatted_tuple)
                self.connect.commit()

    def retrieve_values_from_table(self, name_of_table_to_retrieve_from: str) -> list[tuple]:
        """
        Goes through a given database table and grab a column of data and return those as a list of values.
        :param name_of_table_to_retrieve_from: This will be the name of the table you want to grab values from.
        :return: list of values as a list, not a list of tuples but just a 1D list of each item.
        """
        self.cursor.execute(f'SELECT * FROM {name_of_table_to_retrieve_from}')
        list_of_tuple_of_items = self.cursor.fetchall()

        return list_of_tuple_of_items

    # Built the database with these columns
    def build_database(self):
        self.cursor.execute(
            "CREATE TABLE Study_Fam_People_Currently_In_Focus_Mode (Username text, User_ID integer, "
            "Epoch_End_Time_for_User_Focus_Mode real, Start_of_Session_Time text Number_of_Breaks integer"
            "Break_Length_In_Minutes integer Next_Break_Time real, Number_of_Pomo_Sessions integer, "
            "Current_Pomodoro_Interval integer) ")
        self.connect.commit()

    def add_column(self, column_name: str, column_data_type: str) -> None:
        self.cursor.execute(f"ALTER TABLE Study_Fam_People_Currently_In_Focus_Mode ADD COLUMN {column_name} "
                            f"{column_data_type}")
        self.connect.commit()

    def remove_column(self, column_name: str) -> None:
        self.cursor.execute(f"ALTER TABLE Study_Fam_People_Currently_In_Focus_Mode DROP COLUMN {column_name}")
        self.connect.commit()

    def delete_user_info_from_table(self, name_of_table: str, User_ID: int):
        self.cursor.execute(f"DELETE FROM {name_of_table} WHERE User_ID = {User_ID}")
        self.connect.commit()

    def update_user_info_from_table(self, name_of_table: str, User_ID: int, time_to_update: float,
                                    number_of_breaks: int, break_length: int, next_break_time :int,
                                    number_of_pomo_sessions: int):

        # fetch the latest listing in the db for that user
        self.cursor.execute(f'SELECT * FROM Study_Fam_People_Currently_In_Focus_Mode')
        list_of_tuple_of_items = self.cursor.fetchall()

        for entry in list_of_tuple_of_items:
            if entry[1] == User_ID:

                # format our data to get it ready for updating the db
                user_display_name = entry[0]
                user_session_start_time = entry[3]
                number_of_breaks += entry[4]
                break_length += entry[5]
                next_break_time += entry[6]
                number_of_pomo_sessions += entry[7]

                new_tuple_to_put_in_db = (user_display_name, User_ID, time_to_update, user_session_start_time,
                                          number_of_breaks, break_length, next_break_time, number_of_pomo_sessions)

                # now that we have the new formatted data ready, delete the old listing.
                self.cursor.execute(f"DELETE FROM {name_of_table} WHERE User_ID = {User_ID}")

                # insert new info into the database once we have the formatted data and previous entry deleted.
                self.cursor.execute(f'INSERT INTO {name_of_table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                    new_tuple_to_put_in_db)
                self.connect.commit()

    def check_if_user_in_database(self, user_ID: int):
        self.cursor.execute(f'SELECT * FROM Study_Fam_People_Currently_In_Focus_Mode')
        list_of_tuple_of_items = self.cursor.fetchall()

        for entry in list_of_tuple_of_items:

            if user_ID == entry[1]:
                return entry

        # This will only execute if it went through the whole list of entries and did not find the user's ID listed.
        else:
            return False

    def remove_duplicates(self):
        self.cursor.execute(f'SELECT * FROM Study_Fam_People_Currently_In_Focus_Mode')
        list_of_tuple_of_items = self.cursor.fetchall()

        list_of_entries_without_duplicates = []

        for entry in list_of_tuple_of_items:

            # if this is the first iteration, just add the first entry into the database.
            if not list_of_entries_without_duplicates:
                list_of_entries_without_duplicates.append(entry)

            # if the new list is not empty (i.e. not the first iteration)
            if list_of_entries_without_duplicates:
                for no_duplicate_entry in list_of_entries_without_duplicates:
                    if entry[2] > no_duplicate_entry[2]:
                        list_of_entries_without_duplicates.remove(no_duplicate_entry)
                        list_of_entries_without_duplicates.append(entry)

        # Remove all rows from the table
        self.cursor.execute('DELETE FROM Study_Fam_People_Currently_In_Focus_Mode')

        # Rewrite the rows with the new updated no duplicate info.
        for row in list_of_entries_without_duplicates:
            self.cursor.execute('INSERT INTO Study_Fam_People_Currently_In_Focus_Mode VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?'
                                ')', row)
        self.connect.commit()


# get the current file path we're operating in, so we don't have to hard code this in.
# this also requires that the database be in the same working directory as this script.
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_PATH_AND_NAME = os.path.join(CURRENT_DIRECTORY, "Focus_Mode_Info.db")
database_instance = Database(DB_PATH_AND_NAME)
main_table_name = "Study_Fam_People_Currently_In_Focus_Mode"

import discord
from discord import app_commands
import secrets
from time_modulation import Time_Stuff
from database import Database
import os
import asyncio
import random


class Focus_Bot_Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # Enable the GUILD_MEMBERS intent
        super().__init__(intents=discord.Intents.default())
        self.synced = False  # we use this so the bot doesn't sync commands more than once

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:  # check if slash commands have been synced
            await tree.sync()
            self.synced = True
        print(f"We have logged in as {self.user}.")
        self.loop.create_task(self.role_and_db_removal())

    async def role_and_db_removal(self):
        await self.wait_until_ready()

        server_id = secrets.discord_bot_credentials["Server_ID_for_Study_Fam"]
        guild = client.get_guild(server_id)

        while not self.is_closed():

            # This is a list of tuples, where each item in the tuple is a cell in the row.
            database_entries = database_instance.retrieve_values_from_table("Study_Fam_People_Currently_In_Focus_Mode")

            # make sure the list is not empty
            if database_entries:

                for entry in database_entries:
                    current_time = Time_Stuff.get_current_time_in_epochs()
                    current_user = await guild.fetch_member(entry[1])
                    Focus_Role_object = discord.utils.get(guild.roles, name="Focus")

                    if not entry[6]:

                        if entry[2] <= current_time:
                            await current_user.remove_roles(Focus_Role_object)
                            database_instance.delete_user_info_from_table(
                                name_of_table="Study_Fam_People_Currently_In_Focus_Mode",
                                User_ID=entry[1])

                    else:
                        # if the current time is later than our "next break time" in the database, then go on break.
                        if current_time >= entry[6]:
                            await current_user.remove_roles(Focus_Role_object)
                            next_break_time = current_time + Time_Stuff.next_break_time_pomo_default(entry[8])
                            database_instance.update_user_info_from_table("Study_Fam_People_Currently_In_Focus_Mode",
                                                                          entry[1], entry[2], entry[4] - 1,
                                                                          next_break_time, entry[8] + 1)

            await asyncio.sleep(60)


client = Focus_Bot_Client()
tree = app_commands.CommandTree(client)
Focus_Role_int: int = secrets.discord_bot_credentials["Focus_Role_ID"]

# get the current file path we're operating in, so we don't have to hard code this in.
# this also requires that the database be in the same working directory as this script.
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_PATH_AND_NAME = os.path.join(CURRENT_DIRECTORY, "Focus_Mode_Info.db")
database_instance = Database(DB_PATH_AND_NAME)


@tree.command(name="focus_mode_in_x_minutes", description="Gives user focus mode role without breaks. Best for short "
                                                          "periods of study time.")
async def FocusMode(interaction: discord.Interaction, minutes: int):
    Focus_Role_object = interaction.guild.get_role(Focus_Role_int)
    appropriate_response: str = Time_Stuff.time_responses(minutes)

    if minutes > 1440 or minutes < 0:
        await interaction.response.send_message(appropriate_response, ephemeral=True)

    else:
        user_info_from_db = database_instance.check_if_user_in_database(interaction.user.id)

        # check the database to see if they are just updating their current time left. If not, then create a new entry.
        # if they are updating their time, make sure it's only adding more time, not lessening their time.
        if user_info_from_db:
            await interaction.response.defer()

            new_time = Time_Stuff.add_time(Time_Stuff.get_current_time_in_epochs(), minutes)

            if new_time > user_info_from_db[2]:
                await interaction.followup.send(content=appropriate_response, ephemeral=True)
                database_instance.update_user_info_from_table("Study_Fam_People_Currently_In_Focus_Mode",
                                                              interaction.user.id, new_time, 0, 0, 0, 0, 0)

        # This will execute if the user is not in the database already. Thus, the user_info_from_db value is False.
        elif not user_info_from_db:
            await interaction.response.send_message(appropriate_response, ephemeral=True)
            await interaction.user.add_roles(Focus_Role_object)
            print(f"Successfully given Focus role to {interaction.user.display_name}")

            username = interaction.user.display_name
            user_id = interaction.user.id
            end_time_for_user_session = Time_Stuff.add_time(Time_Stuff.get_current_time_in_epochs(), minutes)
            start_time_for_user_session = Time_Stuff.convert_epochs_to_human_readable_time(
                Time_Stuff.get_current_time_in_epochs())

            user_info_tuple_to_log_to_database = (username, user_id, end_time_for_user_session,
                                                  start_time_for_user_session)

            database_instance.log_to_DB(user_info_tuple_to_log_to_database, "Study_Fam_People_Currently_In_Focus_Mode")


@tree.command(name="focus_mode_pomo_method", description="Gives user focus mode for X amount of pomo sessions.")
async def focus_mode_pomo(interaction: discord.Interaction, pomo_sessions: int, study_length: int,
                          short_break_length: int, long_break_length: int):
    Focus_Role_object = interaction.guild.get_role(Focus_Role_int)

    user_info_from_db = database_instance.check_if_user_in_database(interaction.user.id)

    current_time = Time_Stuff.get_current_time_in_epochs()

    pomo_length = Time_Stuff.pomodoro_session_length(study_length, short_break_length,
                                                     long_break_length, pomo_sessions)

    # check the database to see if they are just updating their current time left. If not, then create a new entry.
    # if they are updating their time, make sure it's only adding more time, not lessening their time.
    if user_info_from_db:
        await interaction.response.defer()
        new_time = user_info_from_db[2] + pomo_length
        new_pomo_amount = user_info_from_db[7] + pomo_sessions
        new_number_of_breaks = user_info_from_db[4] + (pomo_sessions * 4)
        database_instance.update_user_info_from_table("Study_Fam_People_Currently_In_Focus_Mode",
                                                      interaction.user.id, new_time, current_time,
                                                      new_number_of_breaks, 0, new_pomo_amount, user_info_from_db[8])
        await interaction.followup.send(content="Your pomodoro session(s) have been added & updated.", ephemeral=True)

    else:
        await interaction.response.defer()
        end_time = current_time + pomo_length
        next_break_time = current_time + 5.0
        number_of_breaks = pomo_sessions * 4
        user_data_to_log = (interaction.user.display_name, interaction.user.id, end_time, current_time,
                            number_of_breaks, 0, next_break_time, pomo_sessions, 1)
        database_instance.log_to_DB(user_data_to_log, "Study_Fam_People_Currently_In_Focus_Mode")
        await interaction.user.add_roles(Focus_Role_object)


@tree.command(name="time_left_in_focus", description="This will display how much time you have left in focus mode.")
async def display_time_left_for_user(interaction: discord.Interaction):
    database_entries = database_instance.retrieve_values_from_table("Study_Fam_People_Currently_In_Focus_Mode")

    current_time = Time_Stuff.get_current_time_in_epochs()

    for entry in database_entries:

        if interaction.user.id in entry:
            time_left_in_minutes = Time_Stuff.how_many_minutes_apart(entry[2], current_time)

            await interaction.response.send_message(f"You have {time_left_in_minutes} minutes left in Focus Mode.",
                                                    ephemeral=True)
    else:
        await interaction.response.send_message("You are not in the Focus mode database currently.", ephemeral=True)


@tree.command(name="display_all_in_focus_mode", description="Displays all of the users currently in Focus Mode")
async def display_all_in_focus_mode(interaction: discord.Interaction):
    database_entries = database_instance.retrieve_values_from_table("Study_Fam_People_Currently_In_Focus_Mode")

    string_to_send_to_users = "Here is the list of users currently in Focus Mode: \n" \
                              "(Note that times listed are in Eastern time (UTC - 5:00) in 24h time format)\n\n"

    for entry in database_entries:
        string_to_send_to_users += f"User's name: {entry[0]}, \n"
        string_to_send_to_users += f"User's session start time: {entry[3]}, \n"
        string_to_send_to_users += f"User's session end time: " \
                                   f"{Time_Stuff.convert_epochs_to_human_readable_time(entry[2])}, \n\n"

    await interaction.response.send_message(string_to_send_to_users, ephemeral=False)


@tree.command(name="test_response", description="If the bot is truly online, it will respond back with a response.")
async def test_response(interaction: discord.Interaction):

    roll_the_dice = random.randint(1, 100)

    if roll_the_dice != 90:

        await interaction.response.send_message("I have received a test response and I am working fine!", ephemeral=False)

    else:
        await interaction.response.send_message("Yeah yeah yeah... I'm up, what do you need?", ephemeral=False)


TOKEN = secrets.discord_bot_credentials["API_Key"]
client.run(TOKEN)

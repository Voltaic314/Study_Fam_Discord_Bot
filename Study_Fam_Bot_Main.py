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

                    if entry[2] <= current_time:
                        current_user = await guild.fetch_member(entry[1])
                        Focus_Role_object = discord.utils.get(guild.roles, name="Focus")
                        await current_user.remove_roles(Focus_Role_object)
                        database_instance.delete_user_info_from_table(
                            name_of_table="Study_Fam_People_Currently_In_Focus_Mode",
                            User_ID=entry[1])

            await asyncio.sleep(60)


client = Focus_Bot_Client()
tree = app_commands.CommandTree(client)
Focus_Role_int: int = secrets.discord_bot_credentials["Focus_Role_ID"]

# get the current file path we're operating in, so we don't have to hard code this in.
# this also requires that the database be in the same working directory as this script.
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_PATH_AND_NAME = os.path.join(CURRENT_DIRECTORY, "Focus_Mode_Info.db")
database_instance = Database(DB_PATH_AND_NAME)


@tree.command(name="focus_mode_in_x_minutes", description="Gives user focus mode role.")
async def FocusMode(interaction: discord.Interaction, minutes: int):
    Focus_Role_object = interaction.guild.get_role(Focus_Role_int)
    appropriate_response: str = Time_Stuff.time_responses(minutes)

    if minutes > 10080 or minutes < 0:
        await interaction.response.send_message(appropriate_response,
                                                ephemeral=True)

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
                                                              interaction.user.id, new_time)

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

            user_info_tuple_to_log_to_database = (username, user_id, end_time_for_user_session, start_time_for_user_session)
            database_instance.log_to_DB(user_info_tuple_to_log_to_database, "Study_Fam_People_Currently_In_Focus_Mode")


@tree.command(name="time_left_in_focus", description="This will display how much time you have left in focus mode.")
async def display_time_left_for_user(interaction: discord.Interaction):
    database_entries = database_instance.retrieve_values_from_table("Study_Fam_People_Currently_In_Focus_Mode")

    current_time = Time_Stuff.get_current_time_in_epochs()

    for entry in database_entries:

        if interaction.user.id in entry:
            time_left = Time_Stuff.how_many_minutes_apart(entry[2], current_time)
            minutes = time_left[0]
            hours = time_left[1]
            days = time_left[2]

            await interaction.response.send_message(f"You have {days} days, {hours} hours, and {minutes} minutes left "
                                                    f"in Focus Mode.", ephemeral=True)

    else:
        await interaction.response.send_message("You are not in the Focus mode database currently.", ephemeral=True)


@tree.command(name="display_all_in_focus_mode", description="Displays all of the users currently in Focus Mode")
async def display_all_in_focus_mode(interaction: discord.Interaction):
    database_entries = database_instance.retrieve_values_from_table("Study_Fam_People_Currently_In_Focus_Mode")

    if database_entries:

        string_to_send_to_users = "Here is the list of users currently in Focus Mode: \n" \
                                  "(Note that times listed are in Eastern time (UTC - 5:00) in 24h time format)\n\n"

        for entry in database_entries:
            string_to_send_to_users += f"User's name: {entry[0]}, \n"
            string_to_send_to_users += f"User's session start time: {entry[3]}, \n"
            string_to_send_to_users += f"User's session end time: " \
                                       f"{Time_Stuff.convert_epochs_to_human_readable_time(entry[2])}, \n\n"

        await interaction.response.send_message(string_to_send_to_users, ephemeral=False)

    else:
        string_to_send_to_users = "There are currently no users in Focus mode via the bot commands."
        await interaction.response.send_message(string_to_send_to_users, ephemeral=False)


@tree.command(name="test_response", description="If the bot is truly online, it will respond back with a response.")
async def test_response(interaction: discord.Interaction):

    roll_the_dice = random.randint(1, 100)

    if roll_the_dice != 90:

        await interaction.response.send_message("I have received a test response and I am working fine!", ephemeral=False)

    else:
        await interaction.response.send_message("Yeah yeah yeah... I'm up, what do you need?", ephemeral=False)


@tree.command(name="give_max_focus_time", description="Warning, this will give you the focus role for a week straight.")
async def give_max_focus_time(interaction: discord.Interaction):
    Focus_Role_object = interaction.guild.get_role(Focus_Role_int)
    appropriate_response: str = Time_Stuff.time_responses(10080)

    user_info_from_db = database_instance.check_if_user_in_database(interaction.user.id)
    current_time = Time_Stuff.get_current_time_in_epochs()
    number_of_seconds_in_a_week = 604800
    max_time = current_time + number_of_seconds_in_a_week
    time_to_put_user_in_focus = max_time

    # if the user is in the database already, just update their time.
    if user_info_from_db:
        await interaction.response.defer()

        if time_to_put_user_in_focus > user_info_from_db[2]:
            await interaction.followup.send(content=appropriate_response, ephemeral=True)
            database_instance.update_user_info_from_table("Study_Fam_People_Currently_In_Focus_Mode",
                                                          interaction.user.id, time_to_put_user_in_focus)

    # if the user is not already in the database, create an entry with the max focus time as their focus period.
    else:
        await interaction.response.send_message(appropriate_response, ephemeral=True)
        await interaction.user.add_roles(Focus_Role_object)
        print(f"Successfully given Focus role to {interaction.user.display_name}")

        username = interaction.user.display_name
        user_id = interaction.user.id
        end_time_for_user_session = time_to_put_user_in_focus
        start_time_for_user_session = Time_Stuff.convert_epochs_to_human_readable_time(current_time)
        user_info_tuple_to_log_to_database = (username, user_id, end_time_for_user_session, start_time_for_user_session)
        database_instance.log_to_DB(user_info_tuple_to_log_to_database, "Study_Fam_People_Currently_In_Focus_Mode")


@tree.command(name="remove_user_focus_override", description="Removes a user from focus role and their database entry "
                                                             "(mod only)")
async def remove_user_focus_override(interaction: discord.Interaction, user_to_be_removed: discord.User):
    await interaction.response.defer()
    server_id = secrets.discord_bot_credentials["Server_ID_for_Study_Fam"]
    guild = client.get_guild(server_id)
    member = interaction.user
    focus_role_id = secrets.discord_bot_credentials["Focus_Role_ID"]
    mod_role_id = secrets.discord_bot_credentials["Server_Mod_Role_ID"]
    botmod_role_id = secrets.discord_bot_credentials["Server_Botmod_Role_ID"]
    admin_role_id = secrets.discord_bot_credentials["Server_Admin_Role_ID"]

    # All we care about is if the user has the correct role, out of the 3 roles above, as long as they have at least one
    user_doing_command_has_correct_authorization = discord.utils.get(member.roles, id=mod_role_id) or discord.utils.get(
        member.roles, id=botmod_role_id) or discord.utils.get(member.roles, id=admin_role_id)

    if user_doing_command_has_correct_authorization:
        user_to_be_removed_has_focus_role_currently = discord.utils.get(member.roles, id=focus_role_id)
        user_is_in_db = database_instance.check_if_user_in_database(user_to_be_removed.id)

        if user_to_be_removed_has_focus_role_currently:
            current_user = await guild.fetch_member(user_to_be_removed.id)
            Focus_Role_object = discord.utils.get(guild.roles, name="Focus")
            await current_user.remove_roles(Focus_Role_object)
            print("User has been removed from the focus role")

        if user_is_in_db:
            database_instance.delete_user_info_from_table("Study_Fam_People_Currently_In_Focus_Mode",
                                                          user_to_be_removed.id)
            print("User has been removed from the database")

        appropriate_response = f"{user_to_be_removed.mention} has been removed from the database and set to not be in focus anymore!"
        await interaction.followup.send(content=appropriate_response, ephemeral=True)

    else:
        appropriate_response = "You do not have an authorized role to do this, sorry."
        await interaction.followup.send(content=appropriate_response, ephemeral=True)

TOKEN = secrets.discord_bot_credentials["API_Key"]
client.run(TOKEN)

'''
Author: Logan Maupin

This module houses all the slash commands for study bot. :) 
'''
import os
import config 
import discord
from discord_utility_functions import *
from study_bot_client import Study_Bot_Client
from file_processing import File_Processing
from advice import Advice
import asyncio

client = Study_Bot_Client()
tree = discord.app_commands.CommandTree(client)
os.chdir(client.script_dir)
database_file_name_and_path = File_Processing.return_file_name_with_current_directory(
    "Focus_Mode_Info.db")
database_instance = Database(database_file_name_and_path)


def generate_starboard_embed(message, star_count):
    starboard_message = discord.Embed(
        title="Starred Message",
        description=f"New Star Count: {star_count}\n{message.content}",
        color=0xFFFF00  # Yellow color
    )
    starboard_message.set_author(name=f"{message.author.display_name}", icon_url=message.author.avatar_url)
    starboard_message.add_field(name="Source", value=f"[Jump!]({message.jump_url})")
    starboard_message.set_footer(text=f"{message.id} • {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check for message attachments (images) and add them to the embed.
    if message.attachments:
        image_url = message.attachments[0].url  # Assuming one attachment per message
        starboard_message.set_image(url=image_url)

    return starboard_message


def get_special_emote_count(message: discord.Reaction.message) -> dict[str, int]:
    '''
    This function iterates through the emoji reactions of a message to get potential matches
    for special emote cases. If certain emotes are found, they are added to the count. 
    In this case, we have to use specific emote IDs because if someone adds 2 different hypers
    emotes to a message, we don't want that to count for 2 reactions of that emote. 

    Parameters: 
    message: a discord message object. preferably one from the Reaction model, but I think
    any would work. 

    Returns: dictionary where the keys are strings of the emote's ID, and the values are
    the number of times that specific emote showed up. 
    '''

    special_emote_names_and_ids = {'star': 0, 'Hypers': 0, 'EzPepe': 0}

    special_emote_counts = {'star': 0, 'Hypers': 0, 'EzPepe': 0}

    # get the message reaction counts
    for emoji in message.reactions:
        emoji_name = emoji.emoji.name if emoji.custom_emoji else emoji.emoji
        emote_is_special = emoji_name in special_emote_counts.keys()
        if emote_is_special:
            special_emote_counts[emoji_name] = emoji.count

    return special_emote_counts


# TODO: Implement the highlights channel reaction handling
# @client.event
# async def on_reaction_add(reaction, user):
    # post_to_highlights_threshold = 5

    # define our terms
    # message = reaction.message
    # special_emote_counts = get_special_emote_count(message=message)

    # special conditions
    #over_react_threshold = reaction.count > post_to_highlights_threshold

    

    # we_should_post_this_message = all([])
    

    # Send the embed to the starboard channel.
    # await starboard_channel.send(embed=starboard_message)


@tree.command(name="focus_mode_in_x_minutes", description="Gives user focus mode role.")
async def FocusMode(interaction: discord.Interaction, minutes: int):
    Focus_Role_object = interaction.guild.get_role(client.Focus_Role_int)
    appropriate_response: str = Time_Stuff.time_responses(minutes)

    if minutes > 10080 or minutes < 0:
        await interaction.response.send_message(appropriate_response, ephemeral=True)

    else:
        user_info_from_db = database_instance.check_if_user_in_database(
            interaction.user.id)

        # check the database to see if they are just updating their current time left. If not, then create a new entry.
        # if they are updating their time, make sure it's only adding more time, not lessening their time.
        if user_info_from_db:
            await interaction.response.defer()
            seconds = minutes * 60

            new_time = Time_Stuff.get_current_time_in_epochs() + seconds

            if new_time > user_info_from_db[2]:
                await interaction.followup.send(content=appropriate_response, ephemeral=True)
                database_instance.update_user_info_from_focus_table(
                    interaction.user.id, new_time)

        # This will execute if the user is not in the database already. Thus, the user_info_from_db value is False.
        elif not user_info_from_db:
            await interaction.response.send_message(appropriate_response, ephemeral=True)
            await interaction.user.add_roles(Focus_Role_object)
            print(
                f"Successfully given Focus role to {interaction.user.display_name}")

            # set up our variables into a human-readable format, so it's clear what order things go into the database.
            username = interaction.user.display_name
            user_id = interaction.user.id
            seconds = minutes * 60
            end_time_for_user_session = Time_Stuff.get_current_time_in_epochs() + seconds
            start_time_for_user_session = Time_Stuff.convert_epochs_to_human_readable_time(
                Time_Stuff.get_current_time_in_epochs())
            user_info_tuple_to_log_to_database = (
                username, user_id, end_time_for_user_session, start_time_for_user_session)

            # now time to actually log all of that to the database.
            database_instance.log_to_DB(
                user_info_tuple_to_log_to_database, "Study_Fam_People_Currently_In_Focus_Mode")


@tree.command(name="time_left_in_focus", description="This will display how much time you have left in focus mode.")
async def display_time_left_for_user(interaction: discord.Interaction):
    database_entries = database_instance.retrieve_values_from_table(
        "Study_Fam_People_Currently_In_Focus_Mode")

    current_time = Time_Stuff.get_current_time_in_epochs()

    if database_entries:

        for entry in database_entries:

            if interaction.user.id in entry:
                time_left = Time_Stuff.how_many_minutes_apart(
                    entry[2], current_time)
                minutes = time_left[0]
                hours = time_left[1]
                days = time_left[2]

                await interaction.channel.send(
                    f"{interaction.user.mention} - You have {days} days, {hours} hours, and {minutes} minutes left "
                    f"in Focus Mode.")

            else:
                await interaction.channel.send(
                    f"{interaction.user.mention} - You are not in the Focus mode database currently.")


@tree.command(name="display_all_in_focus_mode", description="Displays all of the users currently in Focus Mode")
async def display_all_in_focus_mode(interaction: discord.Interaction):
    string_to_send_to_users = ""
    Focus_Role_Object = interaction.guild.get_role(client.Focus_Role_int)

    # builds the list of users in focus from the database and in the line after, all the users who have focus that are
    # not in the database too.
    database_entries = database_instance.retrieve_values_from_table(
        "Study_Fam_People_Currently_In_Focus_Mode")

    # This is a list of member objects that are not in the database. It compares the role members' IDs with the
    # IDs in the list of tuples.
    all_focus_members = [
        member for member in interaction.guild.members if Focus_Role_Object in member.roles]
    non_database_users_in_focus = [member for member in all_focus_members if member.id
                                   not in [user[1] for user in database_entries]]

    # if there are no users with the focus role at all, then just say that.
    if not Focus_Role_Object.members:
        string_to_send_to_users += "There are currently no users in focus mode right now."
        await interaction.channel.send(string_to_send_to_users)

    else:
        # if there are any users who had the focus role via the bot, list their info out.
        if database_entries:

            # setting up the initial string
            string_to_send_to_users = "Here is the list of users currently in Focus Mode: \n" \
                                      "(Note that times listed are in Eastern time (UTC - 5:00) in 24h time format)\n\n"

            # format the string to be sent to the channel for each user.
            for entry in database_entries:
                string_to_send_to_users += f"User's name: {entry[0]}, \n"
                string_to_send_to_users += f"User's session start time: {entry[3]}, \n"
                string_to_send_to_users += f"User's session end time: " \
                                           f"{Time_Stuff.convert_epochs_to_human_readable_time(entry[2])}, \n\n"

        # for anyone else who is in focus not via the bot, list them out too.
        if non_database_users_in_focus:
            string_to_send_to_users += "Users in focus (not in the database) include: \n"
            for user in non_database_users_in_focus:
                string_to_send_to_users += f"{user.display_name}\n"

        # finally, send the message to the channel that we've spent all this time building.
        await interaction.channel.send(content=string_to_send_to_users)


@tree.command(name="test_response", description="If the bot is truly online, it will respond back with a response.")
async def test_response(interaction: discord.Interaction):
    await interaction.response.send_message("I have received a test response and I am working fine!",
                                            ephemeral=False)


@tree.command(name="give_max_focus_time", description="Warning, this will give you the focus role for a week straight.")
async def give_max_focus_time(interaction: discord.Interaction):
    Focus_Role_object = interaction.guild.get_role(client.Focus_Role_int)
    appropriate_response: str = Time_Stuff.time_responses(10080)
    user_info_from_db = database_instance.check_if_user_in_database(
        interaction.user.id)
    current_time = Time_Stuff.get_current_time_in_epochs()
    number_of_seconds_in_a_week = 604800
    max_time = current_time + number_of_seconds_in_a_week
    time_to_put_user_in_focus = max_time

    # if the user is in the database already, just update their time.
    if user_info_from_db:
        await interaction.response.defer()

        if time_to_put_user_in_focus > user_info_from_db[2]:
            await interaction.followup.send(content=appropriate_response, ephemeral=True)
            database_instance.update_user_info_from_focus_table(
                interaction.user.id, time_to_put_user_in_focus)

    # if the user is not already in the database, create an entry with the max focus time as their focus period.
    else:
        await interaction.response.send_message(appropriate_response, ephemeral=True)
        await interaction.user.add_roles(Focus_Role_object)
        print(
            f"Successfully given Focus role to {interaction.user.display_name}")

        username = interaction.user.display_name
        user_id = interaction.user.id
        end_time_for_user_session = time_to_put_user_in_focus
        start_time_for_user_session = Time_Stuff.convert_epochs_to_human_readable_time(
            current_time)
        user_info_tuple_to_log_to_database = (
            username, user_id, end_time_for_user_session, start_time_for_user_session)
        database_instance.log_to_DB(
            user_info_tuple_to_log_to_database, "Study_Fam_People_Currently_In_Focus_Mode")


@tree.command(name="remove_user_focus_override", description="Removes a user from focus role and their database entry "
                                                             "(mod only)")
async def remove_user_focus_override(interaction: discord.Interaction, user_to_be_removed: discord.User):
    await interaction.response.defer()
    server_id = config.discord_bot_credentials["Server_ID_for_Study_Fam"]
    guild = client.get_guild(server_id)
    member = interaction.user
    focus_role_id = config.discord_bot_credentials["Focus_Role_ID"]

    # All we care about is if the user has the correct role, out of the 3 roles above, as long as they have at least one
    user_doing_command_has_correct_authorization = user_is_moderator_or_higher(interaction.user.roles)

    if user_doing_command_has_correct_authorization:
        user_to_be_removed_has_focus_role_currently = discord.utils.get(
            member.roles, id=focus_role_id)
        user_is_in_db = database_instance.check_if_user_in_database(
            user_to_be_removed.id)

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


@tree.command(name="give_endless_focus_mode", description="Gives focus mode until a mod pulls you out.")
async def give_endless_focus_mode(interaction: discord.Interaction):
    Focus_Role_object = interaction.guild.get_role(client.Focus_Role_int)
    appropriate_response = "You will now be in focus mode with no set end date. Please message or tag a moderator to " \
                           "be removed from focus."
    await interaction.response.send_message(appropriate_response, ephemeral=True)
    await interaction.user.add_roles(Focus_Role_object)
    print(f"Successfully given Focus role to {interaction.user.display_name}")


@tree.command(name="question_of_the_day", description="Provides a random question of the day")
async def question_of_the_day(interaction: discord.Interaction):
    current_channel = interaction.channel

    # We need to do this if the script is being run in a directory that is different from the working directory.
    questions_list_file_path_and_name = File_Processing.return_file_name_with_current_directory(
        "conversation starters.txt")

    # get our question from the text file
    question_pulled_from_text_file = Text_Processing.get_random_line_from_text_file(
        questions_list_file_path_and_name)

    # send the question of the day to the channel the user typed the command in.
    message_to_send = f"**Question of the Day:** {question_pulled_from_text_file}"
    await current_channel.send(message_to_send)
    await interaction.followup.send("Question sent to channel!")


# This is a function to list out potential duplicate emotes in the server. 
@tree.command(name="find_duplicate_emotes", description="Responds with a list of potential duplicate emotes in the server's emote list")
async def Duplicate_Emote_Command(interaction: discord.Interaction):
    await interaction.response.defer()

    if not user_is_moderator_or_higher(interaction.user.roles):
        interaction.followup.send("You do not have the required permissions!")

    image_save_errors = 0

    # iterate through the emotes and only create a list of emote objects from static image emotes
    emote_list = []
    for emote in interaction.guild.emojis:

        if not emote.animated:
            emote_filename = f'{emote.name} - {emote.id}.jpg'
            emote_list.append(emote)

            file_exists = File_Processing.check_if_file_exists(emote_filename)
            
            if not file_exists:
                try:
                    await emote.save(emote_filename)
                
                # if this error is raised, it didn't actually save the file
                except discord.HTTPException as error:
                    print(f"An HTTPException occurred: {error}")
                    image_save_errors += 1

    emote_hash_dict = generate_hash_dict(emote_list=emote_list)

    emote_and_dupe_dict = find_duplicates_through_hashes(emote_hash_dict=emote_hash_dict)

    emote_dict_contains_values = bool(len(emote_and_dupe_dict.keys()))

    
    if image_save_errors:
        await interaction.channel.send(f'There were {image_save_errors} errors trying to save the emoji images.')

    elif emote_dict_contains_values:

        formatted_string_to_send_to_channel = ''
        formatted_string_to_send_to_channel += f'Found: {len(emote_and_dupe_dict.keys())} emotes with potential duplicates.'
        formatted_string_to_send_to_channel += 'Here are a list of emote names and their potential duplicates to check:'

        for emote, duplicate_list in emote_and_dupe_dict.items():

            duplicate_emote_string = ''
            for duplicate_emote in duplicate_list:
                duplicate_emote_string += f'{duplicate_emote.name} {str(duplicate_emote)} - ID: {duplicate_emote.id}\n'
                await interaction.channel.send(f'Emote: {emote.name} {str(emote)} - ID: {emote.id} \nPotential Duplicate Emotes: \n{duplicate_emote_string}')
                
                # sleep so we don't get rate limited lol
                await asyncio.sleep(1)

    else:
        formatted_string_to_send_to_channel = 'There were no duplicates found!'
        await interaction.channel.send(formatted_string_to_send_to_channel)

    await interaction.followup.send("Request Completed!")


@tree.command(name="get_random_advice", description="Responds with random advice from the advice API.")
async def get_random_advice_for_bot_command(interaction: discord.Interaction):
    await interaction.response.defer()
    advice = Advice(config.advice_api_endpoints).get_random_advice()
    await interaction.channel.send(advice)
    await interaction.followup.send("Advice sent to channel!")


@tree.command(name="extract_text_from_url", description="Extracts website's </p> text for you, writes it to a txt file, and uploads that to the channel.")
async def extract_text_from_url(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    
    text_filename = write_text_to_txt_file_from_url(url=url)
    
    if text_filename:
    
        with open(text_filename, encoding="utf-8") as txt_file:
            txt_file_to_upload = discord.File(
                txt_file, filename=text_filename)
            await interaction.channel.send(content="Here you go!", file=txt_file_to_upload)
            os.remove(text_filename)
            await interaction.followup.send("Website text sent to channel! (Request Fulfilled)")
    
    else:
        await interaction.followup.send(content="I'm sorry. We could not get the websíte's text for some reason... try again later.")
        interaction.response.is_done()

@tree.command(name="transcribe_a_yt_video", description="transcribes a YT video into a txt file then uploads that txt file to the channel.")
async def transcribe_a_yt_video(interaction: discord.Interaction, yt_url: str):
    await interaction.response.defer()

    txt_filename = transcribe_video(yt_url)
    if txt_filename:
        with open(txt_filename, encoding="utf-8") as txt_file:
            txt_file_to_upload = discord.File(txt_file, filename=txt_filename)
            await interaction.channel.send(content="Here you go!", file=txt_file_to_upload)
            os.remove(txt_filename)
            await interaction.followup.send("YT video text sent to channel! (Request fulfilled)")
        
    else:
        await interaction.followup.send(content="I'm sorry. We could not get the video's text for some reason... try again later.")
        interaction.response.is_done()

@tree.command(name="short_term_reminder", description="Send a custom reminder to yourself up to 1440 minutes from now.")
async def short_term_reminder(interaction: discord.Interaction, minutes: int, reminder_message: str):
    await interaction.response.defer()
    if minutes > 1440 or minutes < 1:
        await interaction.followup.send("Please try again with minute values between 1 and 1440")

    reminder_time_in_seconds = minutes * 60
    current_time_in_epochs = Time_Stuff.get_current_time_in_epochs()

    time_to_remind_user = current_time_in_epochs + reminder_time_in_seconds

    info_to_log = (interaction.user.name, interaction.user.id, time_to_remind_user, reminder_message)


    database_instance.log_to_DB(info_to_log, "Reminders")
    await interaction.followup.send(f"Done! You will be reminded of this in {minutes} minutes!", ephemeral=True)
    interaction.response.is_done()


@tree.command(name="long_term_reminder", description="Sends you a custom reminder at the time specified. (ALL TIMES IN EST)")
async def long_term_reminder(interaction: discord.Interaction, date: str, time: str, reminder_message: str):
    await interaction.response.defer()

    format_check = Time_Stuff.check_user_formatting_for_long_term_remiinders(date=date, time=time)

    if "incorrect" in format_check:
    
        if "date" in format_check:
            await interaction.followup.send("Please enter the date format as dd-mm-yyyy with the dashes.")
    
        elif "time" in format_check:
            await interaction.followup.send("Please enter the time format (EST Time) as hh:mm format")
    
    else:

        date_time_in_future_epochs = Time_Stuff.convert_date_time_string_to_strp_object(date=date, time=time).timestamp()

        info_to_log = (interaction.user.name, interaction.user.id, date_time_in_future_epochs, reminder_message)
        database_instance.log_to_DB(info_to_log, "Reminders")
        await interaction.followup.send("You will be reminded at that date and time with your message!")
        interaction.response.is_done()

# this is primarily what handles the debugging messages that get sent to the channel
@client.event
async def on_error(event, *args, **kwargs):
    # Handle exceptions that occur in event handlers
    await client.handle_exception(args[0])

import asyncio
import os
import random

import discord
from discord import app_commands

import config
import find_duplicate_emojis
from write_website_text_from_url import write_text_to_txt_file_from_url
from moderator_check import user_is_moderator_or_higher
from transcribe_a_video_and_save_to_txt import transcribe_video
from file_processing import File_Processing
from database import Database
from text_processing import Text_Processing
from time_modulation import Time_Stuff
from video_processing import Video_Processing
from image_processing import Image_Processing
from advice import Advice
from reel import Reel


class Focus_Bot_Client(discord.Client):
    def __init__(self):

        # set up our bot intents
        intents = discord.Intents.default()
        intents.members = True  # Enable the GUILD_MEMBERS intent
        intents.messages = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(intents=intents)

        # we use this so the bot doesn't sync commands more than once
        self.synced = False

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.SELF_CARE_CHANNEL_ID = config.discord_bot_credentials["Self_Care_Channel_ID"]
        self.server_id = config.discord_bot_credentials["Server_ID_for_Study_Fam"]
        self.user_id = config.discord_bot_credentials["Client_ID"]
        self.Focus_Role_int = config.discord_bot_credentials["Focus_Role_ID"]

    async def get_activity_object(self) -> object:
        # setup the advice variables and set the daily status to whatever the advice is
        advice_endpoints = config.advice_api_endpoints        
        daily_random_advice = Advice(endpoints=advice_endpoints).get_random_advice()
        full_advice_string = f'Advice: {daily_random_advice}'
        advice_to_update = discord.Game(full_advice_string)
        await self.change_presence(activity=advice_to_update)

    async def on_ready(self):
        if not self.synced:  # check if slash commands have been synced
            await tree.sync()
            self.synced = True
        print(f"We have logged in as {self.user}.")

        await self.get_activity_object()

        # manage and sort out the focus users
        self.loop.create_task(self.focus_mode_maintenance())

        # start the self care message posting loop
        self.loop.create_task(self.self_care_reminder_time_loop())

        # start the reminders loop
        self.loop.create_task(self.remind_all_users())

        # clear the void channel with the last bit of this code
        guild = client.get_guild(self.server_id)
        auto_delete_channel_id = config.discord_bot_credentials["Auto_Delete_Channel_ID"]
        auto_delete_channel = guild.get_channel(auto_delete_channel_id)

        five_minutes_in_seconds = 300
        await asyncio.sleep(five_minutes_in_seconds)

        async for message in auto_delete_channel.history(limit=None, oldest_first=True):
            if not message.pinned:
                await message.delete()
                asyncio.sleep(5)

        for thread in auto_delete_channel.threads:
            await thread.delete()
            asyncio.sleep(5)
                
        
    async def focus_mode_maintenance(self):
        await self.wait_until_ready()

        # Passing in our variables to create our objects & object attributes.
        guild = client.get_guild(self.server_id)
        

        while True:

            # This is a list of tuples, where each item in the tuple is a cell in the row.
            database_entries = database_instance.retrieve_values_from_table(
                "Study_Fam_People_Currently_In_Focus_Mode")

            # make sure the list is not empty
            if database_entries:

                for entry in database_entries:
                    current_time = Time_Stuff.get_current_time_in_epochs()
                    Focus_Role_object = discord.utils.get(
                        guild.roles, name="Focus")

                    # check to see if the user is past their expired focus ending time. If so, remove them from the
                    # database and remove their focus role. Do this for every user in the database.
                    if entry[2] <= current_time:
                        current_user = await guild.fetch_member(entry[1])
                        await current_user.remove_roles(Focus_Role_object)
                        database_instance.delete_user_info_from_table(
                            name_of_table="Study_Fam_People_Currently_In_Focus_Mode",
                            User_ID=entry[1])

            await asyncio.sleep(60)

    # Function to start posting messages on a fixed interval (every 2 hours)
    async def self_care_reminder_time_loop(self):
        await self.wait_until_ready()

        # define our variables for later on
        guild = client.get_guild(self.server_id)
        self_care_channel = guild.get_channel(self.SELF_CARE_CHANNEL_ID)
        self_care_message_to_send = "Posture & hydration check! I'm watching you! :eyes:"
        number_of_seconds_in_one_hour = 3600
        number_of_seconds_in_four_hours = number_of_seconds_in_one_hour * 4

        while True:

            last_message_sent_time = await self.get_last_message_time_sent_from_user(user_id=self.user_id,
                                                                                     channel=self_care_channel)

            if not last_message_sent_time:
                # post the self-care reminder to the channel.
                await self_care_channel.send(self_care_message_to_send)

            else:
                last_message_is_older_than_an_hour = Time_Stuff.is_input_time_past_threshold(
                    last_message_sent_time, 3600, True)

                # This is so in case we have to reboot the bot it's not just spamming the channel every single time.
                if last_message_is_older_than_an_hour:

                    # delete the previous message before we post again
                    last_message = await self.get_last_message_from_user(self.user_id, channel=self_care_channel)
                    if last_message:
                        await last_message.delete()

                    # post the self-care reminder to the channel.
                    await self_care_channel.send(self_care_message_to_send)

            # pick a random number of seconds to wait between 1 hour minimum and 4 hours maximum
            # This ensures the bot will never post less than at least 6 times a day, but up to 24 times a day max.
            sleep_time = random.randint(number_of_seconds_in_one_hour, 
                                        number_of_seconds_in_four_hours)

            # sleep until it's time to post again.
            await asyncio.sleep(sleep_time)

    @staticmethod
    def get_users_who_need_to_be_reminded():
        current_time = Time_Stuff.get_current_time_in_epochs()
        database_entries = database_instance.retrieve_values_from_table("Reminders")

        users_that_need_to_be_reminded = []

        for entry in database_entries:
            reminder_time = entry[2]
            if current_time - reminder_time > 0:
                users_that_need_to_be_reminded.append(entry)

        return users_that_need_to_be_reminded

    async def remind_user(self, user_id: int, reminder_message: str):
        user = self.get_user(user_id)
        await user.send(reminder_message)
        database_instance.remove_entry_from_table("Reminders", "User_ID", user_id)

    async def remind_all_users(self):
        await self.wait_until_ready()
        
        while True:
            user_list = self.get_users_who_need_to_be_reminded()
            for user in user_list:

                # define the layout of the tuple to more human readable terms
                user_name = user[0]
                user_id = user[1]
                time_of_reminder = user[2]
                reminder_message = user[3]

                # remind each user one by one
                await self.remind_user(user_id=user_id, reminder_message=reminder_message)
                
                # wait 5 seconds after reminding so we don't get rate limited
                await asyncio.sleep(5)

            # wait 1 min between checking to see who needs to be reminded.
            await asyncio.sleep(60)


    @staticmethod
    async def get_last_message_time_sent_from_user(user_id: int, channel: object):
        channel_history = channel.history(limit=None, oldest_first=False)
        async for message_from_user in channel_history:
            if message_from_user.author.id == user_id and not message_from_user.pinned:
                return message_from_user.created_at.timestamp()

    @staticmethod
    async def get_last_message_from_user(user_id: int, channel: object):
        channel_history = channel.history(limit=None, oldest_first=False)
        async for message_from_user in channel_history:
            if message_from_user.author.id == user_id and not message_from_user.pinned:
                return message_from_user

    async def able_to_post_nofication_message(self, channel):
        bot_id = 1073370831356440680
        time_of_last_message_sent = await self.get_last_message_time_sent_from_user(user_id=bot_id, channel=channel)
        thirty_minutes_in_seconds = 1800
        if time_of_last_message_sent:
            we_havent_posted_since_thirty_min_ago = Time_Stuff.is_input_time_past_threshold(time_of_last_message_sent,
                                                                                            thirty_minutes_in_seconds,
                                                                                            True)
            return we_havent_posted_since_thirty_min_ago

        else:
            return True

    @staticmethod
    async def YT_Video_Transcriptions(message: object) -> None:
    
        video_link = Text_Processing.extract_video_url(message.content)
        Video_Processing.transcribe_yt_video_main(video_link)
        video_title = Video_Processing.get_video_title(video_link)
        transcribed_text_filename = Text_Processing.format_file_name(video_title)
        video_title_for_thread_name = Text_Processing.format_title_of_vid_for_txt_file(video_title)

        thread = await message.create_thread(name=video_title_for_thread_name, 
                                             auto_archive_duration=10080)
        
        with open(transcribed_text_filename, encoding="utf-8") as txt_file:
            txt_file_to_upload = discord.File(
                txt_file, filename=transcribed_text_filename)
            await thread.send(content="Transcription File: ", file=txt_file_to_upload)

        os.remove(transcribed_text_filename)


client = Focus_Bot_Client()
tree = app_commands.CommandTree(client)
os.chdir(client.script_dir)
database_file_name_and_path = File_Processing.return_file_name_with_current_directory(
    "Focus_Mode_Info.db")
database_instance = Database(database_file_name_and_path)


'''
A relic of the past. A proof of concept. A funny idea nonetheless,
but it would not be a permanent fixture. 
'''
# @client.event
# async def on_ready():
#     # generate a random person's image for our daily profile picture
#     img_was_saved = Image_Processing.get_random_image()
#     image_filename = 'Profile_Picture.jpg'

#     # set the profile picture to that image
#     with open(image_filename, 'rb') as image:
#         await client.user.edit(avatar=image.read())

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


@client.event
async def on_reaction_add(reaction, user):
    post_to_highlights_threshold = 5

    # define our terms
    message = reaction.message
    special_emote_counts = get_special_emote_count(message=message)

    # special conditions
    over_react_threshold = reaction.count > post_to_highlights_threshold

    

    we_should_post_this_message = all([])
    

    # Send the embed to the starboard channel.
    # await starboard_channel.send(embed=starboard_message)


async def dr_k_notification_messages(message: discord.Message) -> None:
    # Defining our variables for our function here
    Dr_K_YT_Videos_Content_Ping_Role_ID = 1164018979166240768
    Dr_K_YT_Shorts_Content_Ping_Role_ID = 1164022532379246613
    Dr_K_Twitch_Content_Ping_Role_ID = 1164022602147319899
    Carl_Bot_User_ID = 235148962103951360
    Dr_K_Content_Channel_ID = 1078121853266165870

    # Passing in our variables to create our objects & object attributes.
    guild = client.get_guild(client.server_id)
    Dr_K_YT_Videos_Content_Ping_Role = guild.get_role(Dr_K_YT_Videos_Content_Ping_Role_ID)
    Dr_K_YT_Shorts_Content_Ping_Role = guild.get_role(Dr_K_YT_Shorts_Content_Ping_Role_ID)
    Dr_K_Twitch_Content_Ping_Role = guild.get_role(Dr_K_Twitch_Content_Ping_Role_ID)
    Dr_K_Content_Channel = guild.get_channel(Dr_K_Content_Channel_ID)

    if message.channel.id == Dr_K_Content_Channel_ID and message.author.id == Carl_Bot_User_ID:
        
        if "youtu.be/" in message.content:
            await client.YT_Video_Transcriptions(message=message)
            video_url = Text_Processing.extract_video_url(message_contents=message.content)
            video_id = Text_Processing.extract_vid_id_from_shortened_yt_url(shortened_url=video_url)
            video_is_a_short = Video_Processing.is_yt_video_a_short(video_id=video_id)
            if video_is_a_short:
                notification_message = f"{Dr_K_YT_Shorts_Content_Ping_Role.mention} - Dr. K has uploaded a short!"
                await Dr_K_Content_Channel.send(notification_message)
            
            else:
                notification_message = f"{Dr_K_YT_Videos_Content_Ping_Role.mention} - Dr. K has uploaded a YouTube video!"
                await Dr_K_Content_Channel.send(notification_message)
        
        elif "live" in message.content:
            notification_message = f"{Dr_K_Twitch_Content_Ping_Role.mention} - Dr. K has started a live stream on Twitch!"
            await Dr_K_Content_Channel.send(notification_message)


async def post_instagram_reel_media_url(message: discord.Message) -> int or None:
    '''
    This function will post all of the instagram reel mp4 files of each respective
    reel from the reel urls in the given message.

    Parameters:
    message: a discord.Message object that we can build a thread off of. 

    Returns: int - thread id created from the argument message 
    with the reels posted in the thread. 
    '''
    reel_permalink = Text_Processing.extract_insagram_reel_urls_from_text(input_text=message.content)
    if not reel_permalink:
        return None
    reel = Reel(permalink=reel_permalink)
    await message.reply(content=reel.media_url)


@client.event
async def on_message(message):
    await dr_k_notification_messages(message=message)
    # await post_instagram_reel_media_url(message=message)
    

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
async def Duplicate_Emote_command(interaction: discord.Interaction):
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

    emote_hash_dict = find_duplicate_emojis.generate_hash_dict(emote_list=emote_list)

    emote_and_dupe_dict = find_duplicate_emojis.find_duplicates_through_hashes(emote_hash_dict=emote_hash_dict)

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


TOKEN = config.discord_bot_credentials["API_Key"]
client.run(TOKEN)

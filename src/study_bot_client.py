import asyncio
import os
import sys
import json
import traceback

import discord

from config import *
from text_processing import Text_Processing
from time_modulation import Time_Stuff
from video_processing import YT_Video
from advice import Advice
from discord_utility_functions import *
from database import Database
from file_processing import File_Processing
from response_handler import Response, Warning, Error



class Study_Bot_Client(discord.Client):
    def __init__(self):

        # set up our bot intents
        intents = discord.Intents.default()
        intents.members = True  # Enable the GUILD_MEMBERS intent
        intents.messages = True
        intents.guild_messages = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(intents=intents)

        self.database_file_name_and_path = File_Processing.return_file_name_with_current_directory("Focus_Mode_Info.db")
        self.database_instance = Database(self.database_file_name_and_path)

        # we use this so the bot doesn't sync commands more than once
        self.synced = False

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.server_id = discord_bot_credentials["Server_ID_for_Study_Fam"]
        self.user_id = discord_bot_credentials["Client_ID"]
        self.Focus_Role_int = discord_bot_credentials["Focus_Role_ID"]
        self.logging_channel_id = discord_bot_credentials["Logging_Channel_ID"]
        self.guild = self.get_guild(self.server_id)

    async def get_activity_object(self) -> object:
        # setup the advice variables and set the daily status to whatever the advice is
        advice_endpoints = advice_api_endpoints        
        daily_random_advice = Advice(endpoints=advice_endpoints).get_random_advice()
        full_advice_string = f'Advice: {daily_random_advice}'
        advice_to_update = discord.Game(full_advice_string)
        await self.change_presence(activity=advice_to_update)

    async def on_ready(self):
        if not self.synced:  # check if slash commands have been synced
            await tree.sync()
            self.synced = True
        print(f"We have logged in as {self.user}.")

        try:
            await self.get_activity_object()
        except Exception as e:
            print(f"Error setting activity: {e}")
            pass

        # manage and sort out the focus users
        self.loop.create_task(self.focus_mode_maintenance())

        # start the reminders loop
        self.loop.create_task(self.remind_all_users()) 
        
    async def focus_mode_maintenance(self):
        await self.wait_until_ready()

        # Passing in our variables to create our objects & object attributes.
        guild = self.get_guild(self.server_id)

        while True:

            # This is a list of tuples, where each item in the tuple is a cell in the row.
            database_entries = self.database_instance.retrieve_values_from_table(
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
                        self.database_instance.delete_user_info_from_table(
                            name_of_table="Study_Fam_People_Currently_In_Focus_Mode",
                            User_ID=entry[1])

            await asyncio.sleep(60)

    def get_users_who_need_to_be_reminded(self):
        current_time = Time_Stuff.get_current_time_in_epochs()
        database_entries = self.database_instance.retrieve_values_from_table("Reminders")

        users_that_need_to_be_reminded = []

        for entry in database_entries:
            reminder_time = entry[2]
            if current_time >= reminder_time:
                users_that_need_to_be_reminded.append(entry)

        return users_that_need_to_be_reminded

    async def remind_user(self, user_id: int, reminder_message: str, reminder_epoch: float):
        try:
            user = self.get_user(user_id) or await self.fetch_user(user_id)
            await user.send(f"⏰ Reminder: {reminder_message}")
            self.database_instance.delete_reminder(user_id, reminder_epoch)
        except discord.Forbidden:
            print(f"Cannot DM user {user_id}; removing reminder so it does not retry forever.")
            self.database_instance.delete_reminder(user_id, reminder_epoch)
        except Exception as e:
            print(f"Failed to remind user {user_id}: {e}")

    async def remind_all_users(self):
        await self.wait_until_ready()

        while True:
            user_list = self.get_users_who_need_to_be_reminded()
            for user in user_list:
                user_id = user[1]
                time_of_reminder = user[2]
                reminder_message = user[3]

                await self.remind_user(
                    user_id=user_id,
                    reminder_message=reminder_message,
                    reminder_epoch=time_of_reminder,
                )
                # wait briefly so we don't get rate limited
                await asyncio.sleep(1)

            # wait 30s between checks so short reminders stay reasonably on time
            await asyncio.sleep(30)

    @staticmethod
    async def get_last_message_time_sent_from_user(user_id: int, channel: object):
        if channel is None:
            return None
        channel_history = channel.history(limit=None, oldest_first=False)
        async for message_from_user in channel_history:
            if message_from_user.author.id == user_id and not message_from_user.pinned:
                return message_from_user.created_at.timestamp()

    @staticmethod
    async def get_last_message_from_user(user_id: int, channel: object):
        if channel is None:
            return None
        channel_history = channel.history(limit=None, oldest_first=False)
        async for message_from_user in channel_history:
            if message_from_user.author.id == user_id and not message_from_user.pinned:
                return message_from_user

    async def able_to_post_nofication_message(self, channel) -> bool:
        bot_id = 1073370831356440680
        time_of_last_message_sent = await self.get_last_message_time_sent_from_user(user_id=bot_id, channel=channel)
        thirty_minutes_in_seconds = 1800
        if time_of_last_message_sent:
            return Time_Stuff.is_input_time_past_threshold(time_of_last_message_sent, thirty_minutes_in_seconds, True)
        else:
            return True

    async def get_logging_channel(self) -> discord.abc.Messageable | None:
        channel = self.get_channel(self.logging_channel_id)
        if channel is not None:
            return channel
        try:
            return await self.fetch_channel(self.logging_channel_id)
        except Exception as e:
            print(f"Could not fetch logging channel {self.logging_channel_id}: {e}")
            return None

    @staticmethod
    def _truncate(text: str | None, limit: int = 1000) -> str:
        if not text:
            return "N/A"
        text = str(text)
        return text if len(text) <= limit else text[: limit - 3] + "..."

    async def log_error(
        self,
        *,
        title: str,
        error_type: str | None = None,
        message: str | None = None,
        details: str | None = None,
        metadata: dict | None = None,
        interaction: discord.Interaction | None = None,
        exception: BaseException | None = None,
    ) -> str | None:
        """
        Post structured error details to the logging channel.
        Returns a Jump URL to that log message, or None if logging failed.
        """
        if exception is not None and not details:
            details = "".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )

        meta = dict(metadata or {})
        if interaction is not None:
            meta.setdefault("user_name", str(interaction.user))
            meta.setdefault("user_id", interaction.user.id)
            if interaction.channel is not None:
                meta.setdefault("channel_name", getattr(interaction.channel, "name", str(interaction.channel)))
                meta.setdefault("channel_id", interaction.channel.id)
            if interaction.command is not None:
                meta.setdefault("command", interaction.command.name)
            meta.setdefault("guild_id", interaction.guild_id)

        print(f"[ERROR] {title} | type={error_type} | message={message} | details={details} | meta={meta}")

        channel = await self.get_logging_channel()
        if channel is None:
            return None

        embed = discord.Embed(
            title=title[:256],
            description=self._truncate(message, 4096),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        if error_type:
            embed.add_field(name="Error Type", value=self._truncate(error_type, 1024), inline=True)
        if interaction is not None and interaction.command is not None:
            embed.add_field(name="Command", value=f"`/{interaction.command.name}`", inline=True)
        if meta:
            meta_lines = [f"**{k}:** {v}" for k, v in meta.items()]
            embed.add_field(name="Metadata", value=self._truncate("\n".join(meta_lines), 1024), inline=False)
        if details:
            embed.add_field(name="Technical Details", value=f"```{self._truncate(details, 1000)}```", inline=False)

        try:
            log_message = await channel.send(embed=embed)
            return log_message.jump_url
        except Exception as e:
            print(f"Failed to send error to logging channel: {e}")
            return None

    async def reply_with_logged_error(
        self,
        interaction: discord.Interaction,
        *,
        user_message: str,
        title: str = "Command Error",
        error_type: str | None = None,
        details: str | None = None,
        metadata: dict | None = None,
        exception: BaseException | None = None,
        ephemeral: bool = False,
    ) -> None:
        """Log technical details, then reply to the user with a friendly message + Jump! link."""
        jump_url = await self.log_error(
            title=title,
            error_type=error_type,
            message=user_message,
            details=details,
            metadata=metadata,
            interaction=interaction,
            exception=exception,
        )
        content = user_message
        if jump_url:
            content = f"{user_message}\n[Jump!]({jump_url}) for technical details."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(content, ephemeral=ephemeral)
            else:
                await interaction.response.send_message(content, ephemeral=ephemeral)
        except Exception as e:
            print(f"Failed to send user-facing error reply: {e}")

    async def send_content_pings(self, message: discord.Message) -> None:
        message_to_send = get_content_ping_message(message=message)
        
        # if the message is dr k related content
        if message_to_send and 'Error' not in message_to_send:
            current_channel = message.channel
            
            message_was_yt_content = "youtube" in str(message_to_send).lower()

            # do transcriptions if necessary
            # note that if the bot does this route, it will send the ping in the thread instead.
            if message_was_yt_content:
                video_link = Text_Processing.extract_video_url(message.content)
                video = YT_Video(url=video_link)
                if not video.is_watchable:
                    # do nothing
                    return
                
                # if the video is not private or a premiere, transcribe it and send the pings in the thread.
                await self.YT_Video_Transcriptions(message, message_to_send, video)

            else:
                # send the notification message
                await current_channel.send(message_to_send)

    @staticmethod
    async def YT_Video_Transcriptions(message: discord.Message, message_to_send: str, video: YT_Video) -> bool:
        '''
        This function will parse through a message object to get the YT URL, then
        transcribe that YT video to a txt file, and post that following info to a 
        discord thread reply to the message that we looked through. 

        Parameters: 
        message: discord.Message model object. must be an actual message because we 
        are going to make a thread reply to it. 

        Returns: True if the file got transcribed, sent to the thread, and file got removed locally.
        '''

        if not video.is_watchable:
            return False
        
        video_is_transcribable = video.is_watchable and not video.is_livestream

        thread_name = Text_Processing.format_title_of_vid_for_txt_file(video.title)

        thread = await message.create_thread(name=thread_name, 
                                             auto_archive_duration=10080)

        content_was_transcribed = False
        if video_is_transcribable:
            content_was_transcribed = video.transcribe_yt_video()
            if not content_was_transcribed:
                print("content was not able to be transcribed")
                return False

            transcript_filename = Text_Processing.format_file_name(video.title)

            
            # send the file to the thread in a message
            txt_file = open(transcript_filename, mode="rb")
            txt_file_to_upload = discord.File(txt_file, filename=transcript_filename)
            try:
                await thread.send(content="Transcription File: ", file=txt_file_to_upload)
            except Exception as e:
                print(e)
                traceback.print_exc()
                await self.log_error(
                    title="YT transcription upload failed",
                    error_type=type(e).__name__,
                    message="Failed to upload transcription file to thread.",
                    metadata={
                        "video_url": getattr(video, "url", None),
                        "thread_id": getattr(thread, "id", None),
                        "channel_id": getattr(message.channel, "id", None),
                    },
                    exception=e,
                )
            txt_file.close()

        await thread.send(message_to_send)

        # remove the file now that we've sent it
        if content_was_transcribed:
            os.remove(transcript_filename)
    
        return True


##########################################################################################
client = Study_Bot_Client()
tree = discord.app_commands.CommandTree(client)
os.chdir(client.script_dir)
database_file_name_and_path = File_Processing.return_file_name_with_current_directory(
    "Focus_Mode_Info.db")
database_instance = Database(database_file_name_and_path)


@client.event
async def on_message(message: discord.message.Message):
    if message.author == client.user:
        return # ignore self messages to not cause an infinite loop of processing
    
    await client.send_content_pings(message=message)
    
    # if the user uploaded an image in their message, extract the text and post it in a thread reply.
    # TODO: Fix image transcriptions once we decide the best way to do this.
    '''
    print("Now checking if message has an image...")
    if message.attachments:
        print("Message contains attachments")
        if attachment_img_count(message.attachments):
            print("Yep msg attachments contain images")
            await extract_text_from_incoming_messages_main(message=message)
    '''


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
    await interaction.response.send_message("Yep, I'm alive!",
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
    server_id = discord_bot_credentials["Server_ID_for_Study_Fam"]
    guild = client.get_guild(server_id)
    member = interaction.user
    focus_role_id = discord_bot_credentials["Focus_Role_ID"]

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
    await interaction.response.defer(ephemeral=True)
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
    await interaction.followup.send("Question sent to channel!", ephemeral=True)


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
    advice = Advice(advice_api_endpoints).get_random_advice()
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
    await interaction.response.defer(ephemeral=True)
    if minutes > 1440 or minutes < 1:
        await interaction.followup.send("Please try again with minute values between 1 and 1440", ephemeral=True)
        return

    reminder_time_in_seconds = minutes * 60
    current_time_in_epochs = Time_Stuff.get_current_time_in_epochs()
    time_to_remind_user = current_time_in_epochs + reminder_time_in_seconds

    info_to_log = (interaction.user.name, interaction.user.id, time_to_remind_user, reminder_message)
    database_instance.log_to_DB(info_to_log, "Reminders")
    await interaction.followup.send(f"Done! You will be reminded of this in {minutes} minutes!", ephemeral=True)


@tree.command(name="long_term_reminder", description="Sends you a custom reminder at the time specified. (ALL TIMES IN EST)")
async def long_term_reminder(interaction: discord.Interaction, date: str, time: str, reminder_message: str):
    await interaction.response.defer(ephemeral=True)

    format_check = Time_Stuff.check_user_formatting_for_long_term_reminders(date=date, time=time)

    if "incorrect" in format_check:
        if "date" in format_check:
            await interaction.followup.send("Please enter the date format as dd-mm-yyyy with the dashes.", ephemeral=True)
        elif "time" in format_check:
            await interaction.followup.send("Please enter the time format (EST Time) as hh:mm format", ephemeral=True)
        return

    date_time_in_future_epochs = Time_Stuff.convert_date_time_string_to_strp_object(date=date, time=time).timestamp()
    if date_time_in_future_epochs <= Time_Stuff.get_current_time_in_epochs():
        await interaction.followup.send("That time is already in the past. Please choose a future date/time.", ephemeral=True)
        return

    info_to_log = (interaction.user.name, interaction.user.id, date_time_in_future_epochs, reminder_message)
    database_instance.log_to_DB(info_to_log, "Reminders")
    await interaction.followup.send("You will be reminded at that date and time with your message!", ephemeral=True)

@tree.command(name="embed_video", description="Embeds a video from a URL into the channel.")
async def embed_video(interaction: discord.Interaction, url: str, message: str = '', audio_only: bool = False):
    await interaction.response.defer()
    max_file_size_mb = interaction.guild.filesize_limit / (1024 * 1024)

    msg_to_send = f"Posted by {interaction.user.mention}\n"
    if message:
        msg_to_send += f"Caption: {message}\n"
    msg_to_send += f"Source: <{url}>"

    error_metadata = {
        "url": f"<{url}>",
        "audio_only": audio_only,
        "max_file_size_mb": max_file_size_mb,
    }

    try:
        video = await asyncio.to_thread(Video, url, max_file_size_mb)
    except Exception as e:
        await client.reply_with_logged_error(
            interaction,
            user_message="Couldn't process that video link. Please try again later or with a different URL.",
            title="embed_video init failed",
            error_type="VideoInitError",
            metadata=error_metadata,
            exception=e,
        )
        return

    if not video.init_response.success:
        error = video.init_response.errors[0]
        await client.reply_with_logged_error(
            interaction,
            user_message=error.message,
            title="embed_video metadata failed",
            error_type=error.error_type,
            details=error.details,
            metadata={**error_metadata, **(error.metadata or {})},
        )
        return

    try:
        download_fn = video.download_audio if audio_only else video.download
        download_response = await asyncio.to_thread(download_fn)
        if not download_response.success:
            video.delete_file()
            error = download_response.errors[0]
            await client.reply_with_logged_error(
                interaction,
                user_message=error.message,
                title="embed_video download failed",
                error_type=error.error_type,
                details=error.details,
                metadata={**error_metadata, **(error.metadata or {})},
            )
            return
    except Exception as e:
        video.delete_file()
        await client.reply_with_logged_error(
            interaction,
            user_message="Unfortunately there was an error downloading the video.",
            title="embed_video download exception",
            error_type="DownloadError",
            metadata=error_metadata,
            exception=e,
        )
        return

    if video.exists_locally():
        try:
            video_file = discord.File(video.filename, filename=os.path.basename(video.filename))
            await interaction.channel.send(content=msg_to_send, file=video_file)
            await interaction.delete_original_response()
        except Exception as e:
            await client.reply_with_logged_error(
                interaction,
                user_message="Unfortunately there was an error uploading the video.",
                title="embed_video upload failed",
                error_type="UploadError",
                metadata=error_metadata,
                exception=e,
            )
        finally:
            video.delete_file()
    else:
        video.delete_file()
        await client.reply_with_logged_error(
            interaction,
            user_message="Downloaded file not found.",
            title="embed_video missing file",
            error_type="FileNotFoundError",
            metadata=error_metadata,
        )

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Catch unhandled slash-command exceptions and log them with a Jump! link."""
    original = getattr(error, "original", error)
    await client.reply_with_logged_error(
        interaction,
        user_message="Something went wrong running that command. Mods can check the log for details.",
        title="Unhandled slash command error",
        error_type=type(original).__name__,
        exception=original,
        ephemeral=True,
    )


@client.event
async def on_error(event, *args, **kwargs):
    """Handle exceptions that occur in event handlers."""
    tb = traceback.format_exc()
    print(tb)

    metadata = {"event": event}
    if event == "on_message" and args:
        message = args[0]
        metadata.update({
            "message": getattr(message, "content", None),
            "message_time": str(getattr(message, "created_at", None)),
            "user": str(getattr(message, "author", None)),
            "channel_id": getattr(getattr(message, "channel", None), "id", None),
        })

    jump_url = await client.log_error(
        title=f"Event error: {event}",
        error_type="EventError",
        message=f"An error occurred in `{event}`.",
        details=tb,
        metadata=metadata,
    )
    if jump_url:
        print(f"Logged event error: {jump_url}")


if __name__ == "__main__":
    TOKEN = discord_bot_credentials.get("API_Key", "")
    client.run(TOKEN)

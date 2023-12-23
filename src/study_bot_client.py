import asyncio
import os
import random
import traceback

import discord

import config
from text_processing import Text_Processing
from time_modulation import Time_Stuff
from video_processing import Video
from advice import Advice
from discord_utility_functions import get_content_ping_message, attachment_img_count, extract_text_from_incoming_messages_main
from database import Database
from file_processing import File_Processing



class Study_Bot_Client(discord.Client):
    def __init__(self):

        # set up our bot intents
        intents = discord.Intents.default()
        intents.members = True  # Enable the GUILD_MEMBERS intent
        intents.messages = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(intents=intents)

        self.database_file_name_and_path = File_Processing.return_file_name_with_current_directory("Focus_Mode_Info.db")
        self.database_instance = Database(self.database_file_name_and_path)

        # we use this so the bot doesn't sync commands more than once
        self.synced = False

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.SELF_CARE_CHANNEL_ID = config.discord_bot_credentials["Self_Care_Channel_ID"]
        self.server_id = config.discord_bot_credentials["Server_ID_for_Study_Fam"]
        self.user_id = config.discord_bot_credentials["Client_ID"]
        self.Focus_Role_int = config.discord_bot_credentials["Focus_Role_ID"]
        self.guild = self.get_guild(self.server_id)
        debug_channel_id = 1140698361318625382
        self.debug_channel = self.get_channel(debug_channel_id)

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
        guild = self.get_guild(self.server_id)
        auto_delete_channel_id = config.discord_bot_credentials["Auto_Delete_Channel_ID"]
        auto_delete_channel = guild.get_channel(auto_delete_channel_id)

        five_minutes_in_seconds = 300
        await asyncio.sleep(five_minutes_in_seconds)

        async for message in auto_delete_channel.history(limit=None, oldest_first=True):
            if not message.pinned:
                await message.delete()
                await asyncio.sleep(5)

        for thread in auto_delete_channel.threads:
            await thread.delete()
            await asyncio.sleep(5)
                
        
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

    # Function to start posting messages on a fixed interval (every 2 hours)
    async def self_care_reminder_time_loop(self):
        await self.wait_until_ready()

        # define our variables for later on
        guild = self.get_guild(self.server_id)
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


    async def yearly_progress_bar(self):
        await self.wait_until_ready()

        # define our variables for later on
        guild = self.get_guild(self.server_id)
        self_care_channel = guild.get_channel(self.SELF_CARE_CHANNEL_ID)

        last_message_sent_time = await self.get_last_message_time_sent_from_user(user_id=self.user_id,
                                                                                    channel=self_care_channel)

        if last_message_sent_time:
            last_message_is_older_than_a_day = Time_Stuff.is_input_time_past_threshold(
                last_message_sent_time, 10080, True)

            # This is so in case we have to reboot the bot it's not just spamming the channel every single time.
            if last_message_is_older_than_a_day:

                # delete the previous message before we post again
                last_message = await self.get_last_message_from_user(self.user_id, channel=self_care_channel)
                await last_message.delete()

        progress_bar_img_filename = "progress_bar.png"

        # send the file to the thread in a message
        with open(progress_bar_img_filename, mode='rb') as img_file:
            # prepare the file object
            img_file_to_upload = discord.File(
                img_file, filename=progress_bar_img_filename)
            await self_care_channel.send(content="Yearly progress as of today: ", file=img_file_to_upload)


    ## FIXME: something about reminders doesn't work. I think it's not clearing the people from the database properly.
    ## Not sure what's going on there. This will need to be fixed soon. One day... lol
    def get_users_who_need_to_be_reminded(self):
        current_time = Time_Stuff.get_current_time_in_epochs()
        database_entries = self.database_instance.retrieve_values_from_table("Reminders")

        users_that_need_to_be_reminded = []

        for entry in database_entries:
            reminder_time = entry[2]
            if current_time - reminder_time > 0:
                users_that_need_to_be_reminded.append(entry)

        return users_that_need_to_be_reminded

    async def remind_user(self, user_id: int, reminder_message: str):
        user = self.get_user(user_id)
        await user.send(reminder_message)
        self.database_instance.remove_entry_from_table("Reminders", "User_ID", user_id)

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


                # TODO: turning off reminders for now. This needs to be fixed.
                # remind each user one by one
                # await self.remind_user(user_id=user_id, reminder_message=reminder_message)
                
                # wait 5 seconds after reminding so we don't get rate limited
                # await asyncio.sleep(5)

            # wait 1 min between checking to see who needs to be reminded.
            await asyncio.sleep(60)

    async def handle_exception(self, error):
        traceback_text = " ".join(traceback.format_exception(type(error), error, error.__traceback__))
        await self.debug_channel.send(f"An error occurred:```\n{traceback_text}```")

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

    async def able_to_post_nofication_message(self, channel) -> bool:
        bot_id = 1073370831356440680
        time_of_last_message_sent = await self.get_last_message_time_sent_from_user(user_id=bot_id, channel=channel)
        thirty_minutes_in_seconds = 1800
        if time_of_last_message_sent:
            return Time_Stuff.is_input_time_past_threshold(time_of_last_message_sent, thirty_minutes_in_seconds, True)
        else:
            return True
        

    async def send_content_pings(self, message: discord.Message) -> None:
        message_to_send = get_content_ping_message(message=message)
        
        # if the message is dr k related content
        if message_to_send:
            Dr_K_Content_Channel_ID = 1078121853266165870
            Dr_K_Content_Channel = message.guild.get_channel(Dr_K_Content_Channel_ID)
            
            message_was_yt_content = "YouTube" in message_to_send

            # do transcriptions if necessary
            # note that if the bot does this route, it will send the ping in the thread instead.
            if message_was_yt_content:
                await self.YT_Video_Transcriptions(message=message)

            else:
                # send the notification message
                await Dr_K_Content_Channel.send(message_to_send)

    @staticmethod
    async def YT_Video_Transcriptions(message: discord.Message) -> bool:
        '''
        This function will parse through a message object to get the YT URL, then
        transcribe that YT video to a txt file, and post that following info to a 
        discord thread reply to the message that we looked through. 

        Parameters: 
        message: discord.Message model object. must be an actual message because we 
        are going to make a thread reply to it. 

        Returns: True if the file got transcribed, sent to the thread, and file got removed locally.
        '''
        video_link = Text_Processing.extract_video_url(message.content)
        video = Video(url=video_link)

        content_was_transcribed = video.transcribe_yt_video()
        if not content_was_transcribed:
            print("content was not able to be transcribed")
            return False

        transcript_filename = Text_Processing.format_file_name(video.title)
        thread_name = Text_Processing.format_title_of_vid_for_txt_file(video.title)

        thread = await message.create_thread(name=thread_name, 
                                             auto_archive_duration=10080)
        
        # send the file to the thread in a message
        with open(transcript_filename, encoding="utf-8") as txt_file:
            # prepare the file object
            txt_file_to_upload = discord.File(
                txt_file, filename=transcript_filename)
            await thread.send(content="Transcription File: ", file=txt_file_to_upload)
            message_to_send = get_content_ping_message(message=message)
            await thread.send(message_to_send)

        # remove the file now that we've sent it
        os.remove(transcript_filename)
        return True


client = Study_Bot_Client()
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_message(message):

    print("message was posted to server.")

    await client.send_content_pings(message=message)
    
    print("Message may or may not have been a content posting.")

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
    


if __name__ == "__main__":
    TOKEN = config.discord_bot_credentials["API_Key"]
    client.run(TOKEN)

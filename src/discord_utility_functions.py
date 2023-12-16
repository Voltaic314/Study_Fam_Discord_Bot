'''
Author: Logan Maupin

The purpose of this module is to hold a lot of utility functions 
for the bot so we can split up the files a little more.
'''
# general imports and local files
import os
import config

# import the discord library
import discord

# import specific files for extra utilities
import find_duplicate_emojis
from write_website_text_from_url import write_text_to_txt_file_from_url
from moderator_check import user_is_moderator_or_higher
from transcribe_a_video_and_save_to_txt import transcribe_video

# import class objects from other OOP scripts we made
from study_bot_client import Study_Bot_Client # this is the actual discord bot
from reel import Reel
from content_notification import ContentNotification
from text_processing import Text_Processing
from image_processing import Image_Processing
from time_modulation import Time_Stuff
from database import Database


# set up our client and tree to use in the global namespace for now
client = Study_Bot_Client()
tree = discord.app_commands.CommandTree(client)


def get_content_ping_message(message: discord.Message) -> str:

    carl_alert_msg = ContentNotification(message.content, message.author.id, message.channel.id)
    
    # if the message wasn't actually a real alert, then just return an empty string.
    if not carl_alert_msg.is_content_alert:
        return ''
    
    # Defining our variables for our function here
    Dr_K_YT_Videos_Content_Ping_Role_ID = 1164018979166240768
    Dr_K_YT_Shorts_Content_Ping_Role_ID = 1164022532379246613
    Dr_K_Twitch_Content_Ping_Role_ID = 1164022602147319899

    # Passing in our variables to create our objects & object attributes.
    guild = message.guild
    
    # build our role objects to be used in our f-strings below
    Dr_K_YT_Videos_Content_Ping_Role = guild.get_role(Dr_K_YT_Videos_Content_Ping_Role_ID)
    Dr_K_YT_Shorts_Content_Ping_Role = guild.get_role(Dr_K_YT_Shorts_Content_Ping_Role_ID)
    Dr_K_Twitch_Content_Ping_Role = guild.get_role(Dr_K_Twitch_Content_Ping_Role_ID)
    
    video_is_not_private = not carl_alert_msg.yt_video_is_private

    # note this means member only content won't ping people. 
    # so rip members, but oh well. can't please everyone
    # not without doubling up and making member specific ping roles. 
    if carl_alert_msg.is_yt_video and video_is_not_private:

        # now check to see if it's a normal video or a short
        if carl_alert_msg.video.is_short:
            return f"{Dr_K_YT_Shorts_Content_Ping_Role.mention} - Dr. K has uploaded a YouTube short!"
        
        else:
            return f"{Dr_K_YT_Videos_Content_Ping_Role.mention} - Dr. K has uploaded a YouTube video!"
    
    elif carl_alert_msg.is_twitch_stream:
        return f"{Dr_K_Twitch_Content_Ping_Role.mention} - Dr. K has started a live stream on Twitch!"


async def send_content_pings(message: discord.Message) -> None:
    message_to_send = get_content_ping_message(message=message)
    
    # if the message is dr k related content
    if message_to_send:
        Dr_K_Content_Channel_ID = 1078121853266165870
        Dr_K_Content_Channel = message.guild.get_channel(Dr_K_Content_Channel_ID)
        
        message_was_yt_content = "YouTube" in message_to_send

        # do transcriptions if necessary
        # note that if the bot does this route, it will send the ping in the thread instead.
        if message_was_yt_content:
            await client.YT_Video_Transcriptions(message=message)

        else:
            # send the notification message
            await Dr_K_Content_Channel.send(message_to_send)


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


def attachment_is_img(attachment: discord.Attachment):
    print(attachment.content_type)
    return attachment.content_type == "image"


def attachment_img_count(attachments: discord.Attachment) -> int:
    '''
    This function determines how many images are present in a list of attachments
    in a discord message. If the count is 0, then there were no images posted.
    
    Returns: int - number of images present in the discord message's attachment list.
    '''
    img_count = 0
    for attachment in attachments:
        if attachment_is_img(attachment):
            img_count += 1
    return img_count


async def extract_text_from_images(attachments: discord.Attachment) -> dict[str, str] or None:
    
    # If there were no imgs in the message attachments, don't bother extracting text.
    if not attachment_img_count(attachments=attachments):
        return None

    image_texts = {}

    attachment_counter = 1
    for attachment in attachments:
        if attachment_is_img(attachment):

            # save the img, ocr the image, delete the image, save its text to the dictionary
            await attachment.save(fp=attachment.filename)
            img_text = ' '.join(Image_Processing.get_image_text(attachment.filename))
            os.remove(os.path.abspath(attachment.filename))
            image_texts[f'attachment {attachment_counter}'] = img_text
        
        # regardless of whether the attachment was an image, increase the counter so it makes sense
        # what attachment we are referring to. 
        attachment_counter += 1

    return image_texts


def img_text_does_not_exist(image_text: dict[str, str]):
    '''
    This function checks to make sure that the values of image_text dictionary
    aren't just empty strings
    '''
    return not any(bool(string) for string in image_text.values())


async def create_threads_for_img_attachments(message: discord.Message) -> discord.Thread:
    
    image_texts = await extract_text_from_images(attachments=message.attachments)
    
    # don't make a thread if the images don't contain extractable text.
    if not img_text_does_not_exist(image_text=image_texts):
        thread = await message.create_thread(name='image text')
        return thread

async def post_img_text_to_threads(thread: discord.Thread, image_text: dict[str, str]):
    for name, text in image_text.items():
        thread.send(content=f"{name} text: {text}\n\n")


async def extract_text_from_incoming_messages_main(message: discord.Message) -> None:
    
    if not message.attachments:
        return None
    
    if not attachment_img_count(message.attachments):
        return None

    thread = await create_threads_for_img_attachments(message=message)
    image_texts = await extract_text_from_images(message.attachments)
    await post_img_text_to_threads(thread=thread, image_text=image_texts)

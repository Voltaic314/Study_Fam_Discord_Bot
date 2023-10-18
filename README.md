# Focus_Mode_Discord_Bot
This is just a repository for a discord bot made for our study fam discord server. The focus mode hides all the channels until you have the role removed.  This bot gives and takes away that role.


This python discord bot is a collection of different ever-growing functionalities. 

Current functionalities: 

1. Focus mode - allows the user to go into a focus mode (focus role) that blocks out certain channels from the discord server so that they can spend less time distracted.

2. Auto-Deletion channel functionality. This clears all messages in a channel automatically after they have been sent more than 24 hours ago, unless the message is pinned.

3. Self care reminders - automatically post, at random intervals, for the user to stay hydrated and keep their posture upright. At most this would post every hour, at minimum every 4 hours.

4. Question of the day - this bot will post a conversation starter question of the day from a txt file of given questions. Feel free to supply your own text file here if you wish.

5. Dr K Content Pings for every time healthy gamer uploads a YouTube video. Note that we can tailor the pings specifically for livestreams, shorts, or YouTube videos. We use carl-bot reaction roles to get what the user wants to opt into, then depending on the type of content, we ping those specific roles when that specific content is posted. This allows users to say "I want to be notified only for YT videos but not YT Shorts or Twitch Streams." Which is really handy for them to further customize their user experience. 

6. Emote duplication detection. It can now scan the server's static emotes to determine whether there are duplicate emotes in the server. Like for example, if the server admin uploads emote a, and then eventually emote b, and it turns out that a and b are exactly the same image, even though they may have different IDs and different names. The bot can now detect those. It can also come up with false positives and this is just due to the hashing algorithm I am using & its limitations. but I am working on improving that to where you can tell it to ignore certain emote pairs in the results. I'll fix that eventually!

7. Now the bot can automatically transcribe YT videos and upload the transcription plain text txt files as a thread to the message that got posted announcing the new video from that creator. In this case we have it doing for all of Dr K (healthy gamer) videos when they get uploaded and announced to the server. :) 

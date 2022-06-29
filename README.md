Generates wordclouds for a discord server.

This is not really a bot, so much as it is a message downloader.

1) Create a python virtual environment, python 3.7+
2) Install the requirements from requirements.txt (or just pip install wordcloud sqlalchemy Discord.py)
3) Edit the wordclouds_bot.py file. You'll need to set 3 values at the beginning of the file, your username in discord, your discord user id (turn on development mode in discord, right click your name from a message, click "Copy ID")
4) Run the bot (python src/wordclouds_bot.py). It must be run from the root folder, not from the src folder. 
4) Invite the bot to your server. It needs Read Messages/View Channels, Read Message History, and Send Messages permissions

Now that it is on your server and running on your computer:
1) Type :ingest_messages in a channel in the discord server. This will take potentially a very long time. You can monitor the progress by looking at the console output on the computer running the script. To see how many messages there are in your server, go to the discord search and type in "after:1970-01-01" and look at the results count.
2) After that's done, you can run :mark_spam_messages which will purge messages that look like spam... it is a very shitty algorithm. Feel free to make it not crap. But it seems to mostly work. It is very slow though, so feel free to skip this step if you don't have a lot of spam in your server. But be warned, spam really screws up the wordclouds.
3) Then, type :generate_wordclouds
4) When that's done, go to the channel you'd like them to appear in and type :post_wordclouds


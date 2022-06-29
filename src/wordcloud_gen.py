from faulthandler import cancel_dump_traceback_later
import math
from schema import GetSession, Member, Message, Channel
from sqlalchemy.orm import joinedload
from wordcloud import WordCloud
from collections import defaultdict
from sqlalchemy import desc
import datetime
import json

##CONFIG
#The minimum number of unique words to qualify for a wordcloud
#If a member hasn't said at least this many unique words,
#then a wordcloud will not be generated for them
MESSAGE_COUNT_THRESHOLD = 2000
#If the member hasn't sent a message in the past x days, exclude them and their words from the results
EXCLUDE_INACTIVE_LONGER_THAN = datetime.timedelta(days=30)

#Wordcloud settings
WORDCLOUD_CONFIG = {
    'width': 1920,
    'height': 1080,
    'background_color': "black",
    'max_words': 10000,
    'max_font_size': 260,
    'min_font_size': 10,
    'relative_scaling': 0.65 #Default is .5 which might be better?
}

def generate_word_clouds():
    print("Starting...")

    #get SQLAlchemy session
    session = GetSession()

    #current date
    today = datetime.datetime.utcnow()

    print("Loading all members and their messages from db...")
    #Get all members from the SQL database
    members = session.query(Member).where(Member.is_bot == False).all()

    #Total number of words said by everybody together
    #Example: 39,230,239 words have been said
    total_word_count = 0

    #Number of times each individual word has been said
    #Example: "what" has been said 2394 times
    overall_word_counts = defaultdict(int)

    #Total number of words said by each individual member
    #Example: "willjkeller" has said 170392 words
    member_total_word_count = defaultdict(int)

    #Number of times each individual word has been said by each individual member
    #Example: "willjkeller" has said "what" 32 times
    member_word_counts = defaultdict(lambda: defaultdict(int))

    print("Calculating word counts...")

    #Loop through every single discord message recorded
    for member in members:
        #This will be the last message the user sent (most recent)
        last_msg = member.messages.order_by(desc(Message.date_sent)).first()
        #They might not even have any messages
        if last_msg == None:
            continue
        #Calculate how old their most recent message is
        age = today - last_msg.date_sent
        #If it is over the threshold, we skip them. This user isn't active.
        if age > EXCLUDE_INACTIVE_LONGER_THAN:
            continue
        #Get all the messages from this member
        messages = member.messages.all()
        #If they haven't sent enough messages, skip them.
        #This check should really be done at the word count level, but this should
        #be good enough
        if len(messages) < MESSAGE_COUNT_THRESHOLD:
            continue

        print(f"Calculating word counts by {member.name}...")

        for message in messages:
            #Get the text of the message, split on whitespace (split it into words)
            #and make them lowercase and strip off any leading and/or trailing whitespace
            words = [word.lower().strip() for word in message.text.split()]

            #For each word...
            for word in words:
                #Skip zero length words (shouldn't happen but just in case)
                if len(word) == 0:
                    continue

                #Skip words longer than 20 characters. This is probably spam
                if len(word) > 20:
                    continue

                #If the last character is punctuation (not a letter)
                #and the one before last is a letter
                #then strip off the punctuation at the end
                if len(word) > 1 and not word[-1].isalpha() and word[-2].isalpha():
                    word = word[:-1]
                    #This will fail to catch words that end with multiple punctuations,
                    #such as ellipsis... which means the word will be skipped by a following check
                    #TODO: fix that ^^^

                #Skip all single letters except for I and A
                if len(word) == 1 and word != 'i' and word != 'a':
                    continue

                #Skip all 'words' that contain anything other than alpha or "'"
                #This will preserve words like "isn't" and "can't" and "'em"
                #But skip 'words' like q21qwd390 or ,.qwd,,..g#()@
                if not all(char.isalpha() or char == "'" for char in word):
                    continue

                # #Skip all words that aren't english words
                # if word not in all_real_words:
                #     continue

                #Update the running tally of all words said overall
                total_word_count += 1

                #Update the running tally of all words said by the message sender
                member_total_word_count[member.id] += 1

                #Update the running tally of how many times this word has been said overall
                overall_word_counts[word] += 1

                #Update the running tally of how many times this word has been said by the message sender
                member_word_counts[member.id][word] += 1


    #Get a list of IDs from all members that have said enough words
    member_list = member_word_counts.keys()

    #Frequency with which each word is used overall
    #Example: "The" makes up about 4.323% of all words said
    overall_word_freqs = {}

    #Frequency with which each word is used by each individual member
    #Example: "willjkeller" has said "Radio" so many times that it is 26.234% of all their words
    member_word_freqs = defaultdict(dict)

    print("Calculating overall word frequency...")

    #Calculate overall frequency for each word by dividing
    #the number of time each word has been said by the total
    #number of words said
    for (word, count) in overall_word_counts.items():
        freq = float(count) / total_word_count
        overall_word_freqs[word] = freq

    print("Calculating per-member word frequency...")

    #Now, do the same thing as above, but instead of overall,
    #it is done on a per member basis
    #So, go through all the member ids
    for member_id in member_list:
        #now, for each word that this member has said
        for (word, count) in member_word_counts[member_id].items():
            #calculate the freq by divinging how many times they've said `word`
            #by how many words they've said in total
            freq = float(count) / member_total_word_count[member_id]
            member_word_freqs[member_id][word] = freq

    print("Calculating top 500 overall words...")

    #Sort the overall_word_freqs so that the most frequently used words are first.
    #Then, loop through them, taking just the words (we don't need the freq anymore)
    #Keep taking the words until we have 500 (the top 500 most used)
    #Now, throw them all into a set. This is just for quicker lookups to see if a word is in the top 500
    
    top_500_words = set(word for (word, _) in sorted(overall_word_freqs.items(), key=lambda item: item[1], reverse=True)[:500])

    #This will contain, for each member, a dict of their most frequently used words
    #With some filters applied, see below
    member_top_word_freqs = {}

    print("Filtering and selecting each member's top words...")

    #Time to calculate each member's "semi"-unique most frequently used words
    #For each member...
    for member_id in member_list:
        #List of this member's most frequently used words, sorted such that the first element is the most used
        top_words = [
            word
            for (word, _) in
            sorted(
                member_word_freqs[member_id].items(),
                key=lambda item: item[1],
                reverse=True)
        ]
        #This will contain the "selected" top words for this member
        #See the loop below to understand this
        selected_top_words = {}

        #Go through each word in this member's top words
        #The first will be their most used word; the second, their second.
        #Continuing in that order
        for word in top_words:
            #We are going to exclude many of their top words based
            #on a set of rules seen below

            member_freq = member_word_freqs[member_id][word]

            #Skip all words from the top overall set, unless the user uses the word
            #more than 3x as often as average
            if word in top_500_words:
                overall_freq = overall_word_freqs[word]
                if not member_freq > (overall_freq * 3.0):
                    continue

            #Add the word to the selected top words dict,
            #and set the value to the frequency with which it is used by this member
            selected_top_words[word] = member_freq
        
        #We done are with this member, so put their selected top words
        #into the dict, and move on to the next member (next loop)
        member_top_word_freqs[member_id] = selected_top_words

    #List of wordclouds generated, including the file path
    #The member id, and their .mention string
    wordclouds = []

    #Time to generate the wordclouds
    #Go through each member id
    #use the keys of member_top_word_freqs, since some members may not
    #have had enough words to qualify for a wordcloud

    print("Generating wordcloud images...\n")

    idx = 1
    for member_id in member_top_word_freqs.keys():
        #Pull the member from the DB (just need it for their name)
        member = session.query(Member).filter(Member.id==member_id).one()
        first_msg = member.messages.order_by(Message.date_sent).first()

        print(f"({idx:02d}) Generating wordcloud for '{member.name}'")
        idx += 1

        wordcloud_path = f"wordclouds/{member.name}.png"

        member_stats = {
            'path': wordcloud_path,
            'member_id': member.id,
            'member_name': member.name,
            'member_mention': member.mention_string,
            'member_total_words': member_total_word_count[member.id],
            'member_unique_words': len(member_word_counts[member.id]),
            'member_first_message_date': first_msg.date_sent.date().isoformat(),
            'member_first_message': first_msg.text,
            'member_top_15_words': [w for (w, _) in sorted(member_top_word_freqs[member.id].items(), key=lambda x: x[1], reverse=True)[0:15]]
        }

        #Create a WordCloud object, with initial settings
        wordcloud = WordCloud(**WORDCLOUD_CONFIG)

        #Generate the wordcload from the member's selected most frequently used words
        wordcloud.generate_from_frequencies(member_top_word_freqs[member.id])

        #Make it into an image, and save as a PNG to the wordclouds folder
        image = wordcloud.to_image()

        image.save(wordcloud_path, format="png")
        
        #Add the file path
        #and user info to the info list
        wordclouds.append(member_stats)

    #Save the wordclouds info list in the same folder as the images
    with open('wordclouds/info.json', 'w') as outfile:
        json.dump(wordclouds, outfile, indent=4)




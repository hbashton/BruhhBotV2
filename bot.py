#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import logging
import os
import requests
import subprocess
import time
import urllib
from datetime import datetime
from functools import partial
from json import JSONDecoder
from langdetect import detect
from pytz import timezone
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, Chat, User, Message, Update, ChatMember, UserProfilePhotos, File, ReplyMarkup, TelegramObject
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote_plus, urlencode
from uuid import uuid4

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
def __repr__(self):
    return str(self)

config = configparser.ConfigParser()
config.read('bot.ini')

updater = Updater(token=config['KEYS']['bot_api'])
myusername = config['ADMIN']['username']
dispatcher = updater.dispatcher


hereyago = "Here's a list of commands for you to use:\n"
add_help = "/add to let me moderate a group\n"
rem_help = "/rem to stop me from moderating a group any longer\n"
note_a_help = "\n/note <code>notename</code> to see the contents of a note\n"
note_b_help = "-- /note <code>notename</code> + <code>contents</code> to set the contents of a note\n"
note_c_help = "-- /note lock <code>notename</code> to lock a note  - <b>admins only</b>\n"
note_d_help = "-- /note unlock <code>notename</code> to unlock a note  - <b>admins only</b>\n"
note_e_help = "-- /note clear <code>notename</code> to clear a note  - <b>admins only</b>\n"
note_f_help = "-- /note clearall to clear all normal notes  - <b>admins only</b>\n"
note_g_help = "-- /note clearlock to clear all locked notes  - <b>admins only</b>\n"
kick_help = "/kick @username to kick a user from this chat. They will not be able to join unless added\n"
ban_help = "/ban @username to ban a user from this chat. They will not be able to join unless unbanned\n"
unban_help = "/unban @username to unban a user from this chat. They can join, but will not automatically be added\n"
banall_help = "/banall @username to ban a user from all chats I have on record. This can only be used by the owner of this bot.\n"
unbanall_help = "/unbanall @username to unban a user from all chats I have on record. Only my owner can use this command.\n*This is the only way to undo banall*\n"
promote_help = "/promote @username to give a user the power of a mod\n"
demote_help = "/demote @username to remove mod priveleges from a user\n"
modlist_help = "/modlist to see a list of moderators for this chat!\n"
time_help = "\n/time <code>location</code>  to get the current time and date in that location\n"
help_help = "\n/help to see this message\n--/help <code>command</code> to see information about that command :)"
save_help = "\n/save <code>name</code> + <code>message</code> to save a message\n--Then, use #name to get the message you saved!\n"
get_help = "/get <code>name</code> to retrieve a saved message\n"
lock_help = "\n/lock <code>[sticker, gif, flood, arabic]</code> to lock group setings\n"
unlock_help = "/unlock <code>[sticker, gif, flood, arabic]</code> to unlock group settings\n"
setflood_help = "/setflood <code>int</code> to set the number before a user is kicked (must be between 5 and 10) \n"
settings_help = "\n/settings to see the current group settings\n"
get_help = "/get <code>name</code> to retrieve a saved message\n"
gbanlist_help = "\n/gbanlist to get a list of users banned from all my chats\n"
banlist_help = "\n/banlist to get a list of users banned from this chat\n"
setrules_help = "\n/setrules <code>rules</code> to set the rules for this chat\n"
rules_help = "/rules to get the rules for this chat\n"
standardhelp = add_help + rem_help + promote_help + demote_help + modlist_help + kick_help + ban_help + unban_help + banall_help + unbanall_help + banlist_help + gbanlist_help + lock_help + unlock_help + setflood_help + settings_help + note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help + time_help + save_help + get_help + setrules_help + rules_help
notmaster = "Sup <b>not</b> master. \n"
master = "Sup" + myusername + "\n"
# global functions

def latlong(area):
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address=" + area.replace(" ", "%20"))
    status = response.status_code
    print(status)
    resp_json_payload = response.json()

    if status != 200:
        return "fail", "fail"
    else:
        if resp_json_payload['status'] == "ZERO_RESULTS":
            return "fail", "fail"
        else:
            latitude = resp_json_payload['results'][0]['geometry']['location']['lat']
            longitude = resp_json_payload['results'][0]['geometry']['location']['lng']
            return latitude,longitude

def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat."""
    return [admin.user.id for admin in bot.getChatAdministrators(chat_id)]

def get_user_info(bot, chat_id, user_id, find1, find2):
    if find1:
        return bot.getChatMember(chat_id, user_id)[find1][find2]
    else:
        return bot.getChatMember(chat_id, user_id)[find2]
def get_chat_info(bot, chat_id):
    return bot.getChat(chat_id)

def common_vars(bot, update):
    chat_idstr = str(update.message.chat_id)
    chat_id = update.message.chat_id
    fromid = update.message.from_user.id
    fromidstr = str(update.message.from_user.id)
    return chat_idstr, chat_id, fromid, fromidstr

def loadjson(PATH, filename):
    if not os.path.isfile(PATH) or not os.access(PATH, os.R_OK):
        print ("Either file is missing or is not readable. Creating.")
        name = {}
        with open(filename, 'w') as f:
            json.dump(name, f)
    with open(filename) as f:
        name = json.load(f)
    return name

def dumpjson(filename, var):
    with open(filename, 'w') as f:
        json.dump(var, f)

def owner_admin_mod_check(bot, chat_id, chat_idstr, user_id):
    promoted = loadjson('./promoted.json', "promoted.json")
    if chat_idstr in promoted:
        if user_id in get_admin_ids(bot, chat_id) or (user_id in promoted[chat_idstr]) or user_id == int(config['ADMIN']['id']):
            return "true"
    else:
        if user_id in get_admin_ids(bot, chat_id) or user_id == int(config['ADMIN']['id']):
            return "true"
        else:
            return "false"
def owner_check(bot, chat_id, user_id):
    if user_id == int(config['ADMIN']['id']):
        return "true"
    else:
        return "false"

def getRandomButts(attempt):
    attempt = attempt + 1

    res = requests.get("http://api.obutts.ru/noise/1")
    status = res.status_code
    if status == 200:
        data = json.loads(res.text)[0]

    if not data and attempt <= 3:
        return getRandomButts(attempt)
    return 'http://media.obutts.ru/' + data["preview"]

def getRandomBoobs(attempt):
    attempt = attempt + 1

    res = requests.get("http://api.oboobs.ru/noise/1")
    status = res.status_code
    if status == 200:
        data = json.loads(res.text)[0]
    else:
        data = ""

    if not data and attempt <= 10:
        return getRandomBoobs(attempt)
    return 'http://media.oboobs.ru/' + data["preview"]
# start and help come first

def start(bot, update):
    if update.message.chat.type == "private":

        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Hi. I'm BruhhBot! You can use me to do lots of cool stuff")

        helpall = standardhelp + help_help

        bot.sendMessage(chat_id=update.message.chat_id,
                            text=helpall)

def help_message(bot, update, args):
    standardlist = ["save", "get", "time", "ban", "unban", "kick", "note", "banall", "unbanall", "add", "rem", "promote", "demote", "modlist", "lock", "unlock", "setflood", "settings", "setrules", "rules", "gbanlist", "banlist"]

    args_length = len(args)
    masterlist = standardlist
    helpall = standardhelp + help_help
    if args_length != 0:
        if args_length > 1:
            helpme = "Please only ask about one command. Some commands to consider asking about:\n" + ",\n".join(masterlist)
        else:
            if args[0] in masterlist:
                if args[0] == "note":
                    helpme = note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help
                if args[0] == "ban":
                    helpme = ban_help
                if args[0] == "unban":
                    helpme = unban_help
                if args[0] == "kick":
                    helpme = kick_help
                if args[0] == "time":
                    helpme = time_help
                if args[0] == "promote":
                    helpme = promote_help
                if args[0] == "demote":
                    helpme = demote_help
                if args[0] == "add":
                    helpme = add_help
                if args[0] == "rem":
                    helpme = rem_help
                if args[0] == "banall":
                    helpme = banall_help
                if args[0] == "unbanall":
                    helpme = unbanall_help
                if args[0] == "modlist":
                    helpme = modlist_help
                if args[0] == "save":
                    helpme = save_help
                if args[0] == "get":
                    helpme = get_help
                if args[0] == "lock":
                    helpme = lock_help
                if args[0] == "unlock":
                    helpme = unlock_help
                if args[0] == "setflood":
                    helpme = setflood_help
                if args[0] == "settings":
                    helpme = settings_help
                if args[0] == "gbanlist":
                    helpme = gbanlist_help
                if args[0] == "banlist":
                    helpme = banlist_help
                if args[0] == "rules":
                    helpme = rules_help
                if args[0] == "setrules":
                    helpme = setrules_help
            else:
                helpme = "That's not a command to ask about."
        bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=helpme,
                        parse_mode="HTML")
    else:
        bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=helpall,
                        parse_mode="HTML")

# real stuff
def add(bot, update):
    global moderated
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
    if update.message.chat.type != "private":
        if fromid in get_admin_ids(bot, update.message.chat_id):
            if bot.id in get_admin_ids(bot, update.message.chat_id):
                moderated = loadjson('./moderated.json', "moderated.json")
                if chat_idstr not in moderated.keys():
                    moderated[chat_idstr] = chat_id
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=update.message.chat.title + " added to my records!")
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=update.message.chat.title + " is already in my records")
                with open("moderated.json", 'w') as f:
                    json.dump(moderated, f)
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="I need to be an admin to moderate groups!")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="You gotta be an admin to tell me what to do!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="I only work with groups! Sorry pal")


def rem(bot, update):
    global moderated
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
    if update.message.chat.type != "private":
        if get_user_info(bot, chat_id, fromid, "", "status") == "creator" or owner_check(bot, chat_id, fromid) == "true":
            if bot.id in get_admin_ids(bot, update.message.chat_id):
                moderated = loadjson('./moderated.json', "moderated.json")
                if chat_idstr in moderated.keys():
                    del moderated[chat_idstr]
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=update.message.chat.title + " removed from my records!")
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=update.message.chat.title + " isn't even in my book bro")
                with open("moderated.json", 'w') as f:
                    json.dump(moderated, f)
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="I need to be an admin to moderate groups!")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Umm, pretty sure the creator of this group should tell me whether to leave or not.")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="I only work with groups! Sorry pal")

def receiveMessage(bot, update):
    global idbase
    global moderated
    global banbase
    global promoted
    global locked
    global welcome
    idbase = loadjson('./idbase.json', "idbase.json")

    if update.message.chat.type != "private":
        tguser = str(update.message.from_user.username).lower()
        tgid = str(update.message.from_user.id)
        chat_idstr = str(update.message.chat_id)
        chat_id = update.message.chat_id
        chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)

        moderated = loadjson('./moderated.json', "moderated.json")

        banbase = loadjson('./banbase.json', "banbase.json")

        promoted = loadjson('./promoted.json', "promoted.json")

        locked = loadjson('./locked.json', "locked.json")

        welcome = loadjson('./welcome.json', "welcome.json")

        flooding = loadjson('./flooding.json', "flooding.json")

        if chat_idstr not in welcome.keys():
            welcome[chat_idstr] = {}
            welcome[chat_idstr]["welcome"] = ""
            welcome[chat_idstr]["message"] = ""
        if chat_idstr not in flooding.keys():
            flooding[chat_idstr] = {}
        if chat_idstr not in locked.keys():
            fixlocked(bot, update)
        if chat_idstr not in promoted.keys():
            promoted[chat_idstr] = []
        if chat_idstr not in banbase.keys():
            banbase[chat_idstr] = []
        if "global" not in banbase.keys():
            banbase["global"] = []
        idbase[fromidstr] = tguser
        if fromidstr in banbase[chat_idstr]:
            bot.kickChatMember(chat_id, fromidstr)
        if fromidstr in banbase["global"]:
            bot.kickChatMember(chat_id, fromidstr)
        if update.message.new_chat_member:
            tguser = str(update.message.new_chat_member["username"]).lower()
            tgid = str(update.message.new_chat_member["id"])
            if tgid not in idbase.keys():
                idbase[tgid] = tguser
            else:
                olduser = idbase[tgid]
                if olduser != tguser:
                    idbase[tgid] = tguser
            if tgid in banbase[chat_idstr]:
                bot.kickChatMember(chat_id, tgid)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="@" + tguser + " is not allowed here ^-^")
            if tgid in banbase["global"]:
                bot.kickChatMember(chat_id, tgid)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="@" + tguser + " ....I really don't like them. '_'")
            if welcome[chat_idstr]["welcome"] == "yes":
                if not welcome[chat_idstr]["message"]:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    reply_to_message_id=update.message.message_id,
                                    text="Hi @" + tguser + "! Welcome to " + update.message.chat.title)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    reply_to_message_id=update.message.message_id,
                                    text="Hi @" + tguser + "! " + welcome[chat_idstr]["message"])
        dumpjson("idbase.json", idbase)
        dumpjson("banbase.json", banbase)
        dumpjson("promoted.json", promoted)
        dumpjson("locked.json", locked)
        dumpjson("flooding.json", flooding)
        dumpjson("welcome.json", welcome)

        if update.message.left_chat_member:
            tguser = str(update.message.left_chat_member["username"]).lower()
            tgid = str(update.message.left_chat_member["id"])
            if tgid not in idbase.keys():
                idbase[tgid] = tguser
            else:
                olduser = idbase[tgid]
                if olduser != tguser:
                    idbase[tgid] = tguser
            dumpjson("idbase.json", idbase)
            dumpjson("banbase.json", banbase)
            dumpjson("promoted.json", promoted)
            dumpjson("locked.json", locked)
            dumpjson("flooding.json", flooding)
            dumpjson("welcome.json", welcome)

    receiveLocked(bot, update)
    floodcheck(bot, update)
    if update.message.text:
        if update.message.text[:1] == "#":
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            splitme = update.message.text.split()
            extra = splitme[0]
            extra = extra.replace("#", "", 1)
            saved = loadjson('./saved.json', "saved.json")
            if chat_idstr in saved.keys():
                if extra in saved[chat_idstr].keys():
                    bot.sendMessage(chat_id=update.message.chat_id,
                                            text=extra + ":\n" + saved[chat_idstr][extra])

def receiveLocked(bot, update):
    idbase = loadjson('./idbase.json', "idbase.json")
    tguser = str(update.message.from_user.username).lower()

    if update.message.chat.type != "private":
        chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
        if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "false":
            if bot.id in get_admin_ids(bot, update.message.chat_id):
                if fromidstr not in idbase.keys():
                    idbase[fromidstr] = tguser
                dumpjson("idbase.json", idbase)

                sentlock = loadjson('./sentlock.json', "sentlock.json")
                idbase = loadjson('./idbase.json', "idbase.json")
                if chat_idstr not in sentlock.keys():
                    sentlock[chat_idstr] = {}
                if update.message.document:
                    if update.message.document.mime_type == "video/mp4":
                        if locked[chat_idstr]["gif"] == "yes":
                            if fromidstr not in sentlock[chat_idstr].keys():
                                sentlock[chat_idstr][fromidstr] = 1
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                reply_to_message_id=update.message.message_id,
                                                text="This type of media is not allowed here. <code>1/3</code>",
                                                parse_mode="HTML")
                                dumpjson("sentlock.json", sentlock)

                            else:
                                if sentlock[chat_idstr][fromidstr] == 1:
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                reply_to_message_id=update.message.message_id,
                                                text="This type of media is not allowed here. <code>2/3</code>",
                                                parse_mode="HTML")
                                    sentlock[chat_idstr][fromidstr] = 2
                                    dumpjson("sentlock.json", sentlock)

                                else:
                                    if sentlock[chat_idstr][fromidstr] == 2:
                                        bot.sendMessage(chat_id=update.message.chat_id,
                                                        reply_to_message_id=update.message.message_id,
                                                        text="Gifs are not allowed here.\n" + "@" + idbase[fromidstr] + " kicked.")
                                        bot.kickChatMember(chat_id, fromid)
                                        del sentlock[chat_idstr][fromidstr]
                                        dumpjson("sentlock.json", sentlock)

                if update.message.sticker:
                    if locked[chat_idstr]["sticker"] == "yes":
                        if fromidstr not in sentlock[chat_idstr].keys():
                            sentlock[chat_idstr][fromidstr] = 1
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            reply_to_message_id=update.message.message_id,
                                            text="This type of media is not allowed here. <code>1/3</code>",
                                            parse_mode="HTML")
                            dumpjson("sentlock.json", sentlock)

                        else:
                            if sentlock[chat_idstr][fromidstr] == 1:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                            text="This type of media is not allowed here. <code>2/3</code>",
                                            parse_mode="HTML")
                                sentlock[chat_idstr][fromidstr] = 2
                                dumpjson("sentlock.json", sentlock)

                            else:
                                if sentlock[chat_idstr][fromidstr] == 2:
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    reply_to_message_id=update.message.message_id,
                                                    text="Stickers are not allowed here.\n" + "@" + idbase[fromidstr] + " kicked.")
                                    bot.kickChatMember(chat_id, fromid)
                                    del sentlock[chat_idstr][fromidstr]
                                    dumpjson("sentlock.json", sentlock)

                if locked[chat_idstr]["arabic"] == "yes":
                    if update.message.text:
                        message_text = update.message.text
                        if detect(message_text) == "ar":
                            if fromidstr not in sentlock[chat_idstr].keys():
                                sentlock[chat_idstr][fromidstr] = 1
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                reply_to_message_id=update.message.message_id,
                                                text="Arabic is not allowed here. <code>1/3</code>",
                                                parse_mode="HTML")
                            else:
                                if sentlock[chat_idstr][fromidstr] == 1:
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                reply_to_message_id=update.message.message_id,
                                                text="Arabic is not allowed here. <code>2/3</code>",
                                                parse_mode="HTML")
                                    sentlock[chat_idstr][fromidstr] = 2

                                else:
                                    if sentlock[chat_idstr][fromidstr] == 2:
                                        bot.sendMessage(chat_id=update.message.chat_id,
                                                        reply_to_message_id=update.message.message_id,
                                                        text="Arabic is not allowed here.\n" + "@" + idbase[fromidstr] + " kicked.")
                                        bot.kickChatMember(chat_id, fromid)
                                        del sentlock[chat_idstr][fromidstr]

def floodcheck(bot, update):
    global flooding
    if update.message.chat.type != "private":
        chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
        moderated = loadjson('./moderated.json', "moderated.json")
        if chat_idstr in moderated:
            if bot.id in get_admin_ids(bot, update.message.chat_id):
                flooding = loadjson('./flooding.json', "flooding.json")
                locked = loadjson('./locked.json', "locked.json")
                idbase = loadjson('./idbase.json', "idbase.json")
                if chat_idstr not in flooding.keys():
                    flooding[chat_idstr] = {}
                    flooding[chat_idstr]["floodmember"] = fromidstr
                    dumpjson("flooding.json", flooding)
                    flooding = loadjson('./flooding.json', "flooding.json")
                if "floodmember" not in flooding[chat_idstr].keys():
                     flooding[chat_idstr]["floodmember"] = fromidstr
                if "limit" not in flooding[chat_idstr].keys():
                    flooding[chat_idstr]["limit"] = 10
                if "floodcount" not in flooding[chat_idstr].keys():
                    flooding[chat_idstr]["floodcount"] = 0
                if locked[chat_idstr]["flood"] == "yes":
                    if chat_idstr not in flooding.keys():
                        fixlocked(bot, update)
                    limit = flooding[chat_idstr]["limit"]
                    count = flooding[chat_idstr]["floodcount"]
                    if fromidstr == flooding[chat_idstr]["floodmember"]:
                        if count < limit:
                            flooding[chat_idstr]["floodcount"] += 1
                        else:
                            if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) != "true":
                                promoted = loadjson('./promoted.json', "promoted.json")
                                if chat_idstr in promoted.keys():
                                    if promoted[chat_idstr]:
                                        if fromid not in promoted[chat_idstr]:
                                            bot.sendMessage(chat_id=update.message.chat_id,
                                                            text="Flooding is not allowed here.\n" + "@" + idbase[fromidstr] + " kicked")
                                            bot.kickChatMember(chat_id, fromid)
                                            flooding[chat_idstr]["floodcount"] = 1
                                else:
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    text="Flooding is not allowed here.\n" + "@" + idbase[fromidstr] + " kicked")
                                    bot.kickChatMember(chat_id, fromid)
                                    flooding[chat_idstr]["floodcount"] = 1
                    else:
                        flooding[chat_idstr]["floodmember"] = fromidstr
                        flooding[chat_idstr]["floodcount"] = 1

                dumpjson("flooding.json", flooding)

def modlist(bot, update):
    if update.message.chat.type != "private":
        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr = str(update.message.chat_id)
            chat_title = update.message.chat.title
            moderated = loadjson('./moderated.json', "moderated.json")
            promoted = loadjson('./promoted.json', "promoted.json")
            idbase = loadjson('./idbase.json', "idbase.json")

            if chat_idstr in moderated:
                if chat_idstr in promoted.keys():
                    if promoted[chat_idstr]:
                        for user in promoted[chat_idstr]:
                            for userid, username in idbase.items():
                                if str(user) == userid:
                                    try:
                                        userlist
                                    except NameError:
                                        userlist = "Moderators for " + chat_title + ":\n"
                                    userlist = userlist + "@" + username + "\n"
                    else:
                        userlist = "No moderators for this chat!"
                else:
                    userlist = "No moderators for this chat!"
                try:
                    userlist
                except NameError:
                    userlist = "No moderators for this chat!"
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=userlist)

            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You're the only mod here ;)")
def getglobalbanlist(bot, update):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                global idbase
                global banbase

                banbase = loadjson('./banbase.json', "banbase.json")
                idbase = loadjson('./idbase.json', "idbase.json")

                if "global" not in banbase.keys():
                    msg = "No users globally banned"
                else:
                    if banbase["global"]:
                        msg = ""
                        lst = banbase["global"]
                        length = len(lst)
                        for i in range(0, length):
                            for ID, USER in idbase.items():
                                if ID == banbase["global"][i]:
                                    if not msg:
                                        msg = "Global Banlist" + ":\n"
                                    msg =  msg + "@" + USER + "\n"
                    else:
                        msg = "No users globally banned"
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=msg)
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
def getbanlist(bot, update):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                global idbase
                global banbase

                banbase = loadjson('./banbase.json', "banbase.json")
                idbase = loadjson('./idbase.json', "idbase.json")

                if chat_idstr not in banbase.keys():
                    msg = "No users banned from this chat"
                else:
                    if banbase[chat_idstr]:
                        msg = ""
                        lst = banbase[chat_idstr]
                        length = len(lst)
                        for i in range(0, length):
                            for ID, USER in idbase.items():
                                if ID == banbase[chat_idstr][i]:
                                    if not msg:
                                        msg = "Banlist for " + update.message.chat.title + ":\n"
                                    msg =  msg + "@" + USER + "\n"
                    else:
                        msg = "No users banned from this chat"
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=msg)
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")

def promoteme(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    global idbase
                    global promoted
                    promoted = loadjson('./promoted.json', "promoted.json")
                    idbase = loadjson('./idbase.json', "idbase.json")

                    str_args = ' '.join(args)
                    if "@" in str_args:
                        promoteuser = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user == promoteuser:
                                user_id = tg_id
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name!")
                        if chat_idstr not in promoted.keys():
                            promoted[chat_idstr] = []
                        if user_id:
                            promoteuser = str_args.replace("@", "")
                            if chat_idstr in promoted.keys():
                                if promoted[chat_idstr]:
                                    if user_id not in promoted[chat_idstr]:
                                        promoted[chat_idstr].append(user_id)
                                        bot.sendMessage(chat_id=update.message.chat_id,
                                                        text="User @" + promoteuser + " is now a mod of " + update.message.chat.title + "! Congratulations!")
                                    else:
                                        bot.sendMessage(chat_id=update.message.chat_id,
                                                        text="User @" + promoteuser + " is already a moderator.")
                                else:
                                    promoted[chat_idstr] = []
                                    promoted[chat_idstr] = [user_id]
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    text="User @" + promoteuser + " is now a mod of " + update.message.chat.title + "! Congratulations!")
                            else:
                                promoted[chat_idstr] = []
                                promoted[chat_idstr] = [user_id]
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="User @" + promoteuser + " is now a mod of " + update.message.chat.title + "! Congratulations!")

                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can promote someone with /promote @username")

                    dumpjson("promoted.json", promoted)

                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")

        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You can only promote someone in groups")

def demoteme(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    global idbase
                    global promoted

                    promoted = loadjson('./promoted.json', "promoted.json")
                    idbase = loadjson('./idbase.json', "idbase.json")

                    str_args = ' '.join(args)
                    if "@" in str_args:
                        demoteuser = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user == demoteuser:
                                user_id = tg_id
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name! <b>hint</b> - they must say something for me to get to know them!")
                        if chat_idstr not in promoted.keys():
                                promoted[chat_idstr] = []
                        if user_id:
                            if chat_idstr in promoted.keys():
                                if user_id in promoted[chat_idstr]:
                                    demoteuser = str_args.replace("@", "")
                                    promoted[chat_idstr].remove(user_id)
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    text="User @" + demoteuser + " is no longer a moderator of " + update.message.chat.title + " :(")
                                else:
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    text="User @" + demoteuser + " is not a moderator. Good thing, cause they were about to lose that anyway")
                            else:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="We don't even have any moderators.")
                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can demote someone with /demote @username")
                    dumpjson("promoted.json", promoted)

                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You can only demote someone in groups")

def unbanme(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:

                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    global idbase
                    global banbase

                    banbase = loadjson('./banbase.json', "banbase.json")
                    idbase = loadjson('./idbase.json', "idbase.json")

                    str_args = ' '.join(args)
                    if "@" in str_args:
                        unbanuser = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user == unbanuser:
                                user_id = tg_id
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name!")
                        if chat_idstr not in banbase.keys():
                                banbase[chat_idstr] = []
                        if user_id:
                            if user_id in banbase[chat_idstr]:
                                unbanuser = str_args.replace("@", "")
                                banbase[chat_idstr].remove(user_id)
                                bot.unbanChatMember(chat_id, user_id)
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="User @" + unbanuser + " is welcome in " + update.message.chat.title + " once again :)")
                            else:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="User @" + unbanuser + " is not banned from this chat. Maybe you meant someone else?")
                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can unban someone with /unban @username")
                    dumpjson("banbase.json", banbase)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")

def unbanall(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_check(bot, chat_id, fromid) == "true":
                    global idbase
                    global banbase

                    banbase = loadjson('./banbase.json', "banbase.json")
                    idbase = loadjson('./idbase.json', "idbase.json")

                    str_args = ' '.join(args)
                    if "@" in str_args:
                        unbanuser = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user == unbanuser:
                                user_id = tg_id
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name!")
                        if user_id:
                            if owner_admin_mod_check(bot, chat_id, chat_idstr, user_id) != "true":
                                unbanuser = str_args.replace("@", "")
                                for string, chat in moderated.items():
                                    bot.unbanChatMember(chat, user_id)
                                if user_id in banbase["global"]:
                                    banbase["global"].remove(user_id)
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    text="User @" + unbanuser + " globally unbanned from all my chats!")
                                else:
                                    bot.sendMessage(chat_id=update.message.chat_id,
                                                    text="User @" + unbanuser + " is not globally banned!")
                            else:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="You can't gban mods! &$%^# ")

                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can global unban someone with /unbanall @username")
                    dumpjson("banbase.json", banbase)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only my owner can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")

def banall(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_check(bot, chat_id, fromid) == "true":
                    global idbase
                    global banbase

                    banbase = loadjson('./banbase.json', "banbase.json")
                    idbase = loadjson('./idbase.json', "idbase.json")

                    str_args = ' '.join(args)
                    if "@" in str_args:
                        banuser = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user == banuser:
                                user_id = tg_id
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name!")
                        if user_id:
                            if owner_admin_mod_check(bot, chat_id, chat_idstr, user_id) != "true":
                                banuser = str_args.replace("@", "")
                                for string, chat in moderated.items():
                                    bot.kickChatMember(chat, user_id)
                                banbase["global"] = banbase["global"] + [user_id]
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="User @" + banuser + " globally banned from all my chats!")
                            else:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="You can't gban mods! &$%^# ")

                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can global ban someone with /banall @username")
                    dumpjson("banbase.json", banbase)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only my owner can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")


def banme(bot, update, args):
    if update.message.chat.type != "private":
        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    global idbase
                    global banbase

                    banbase = loadjson('./banbase.json', "banbase.json")
                    idbase = loadjson('./idbase.json', "idbase.json")

                    str_args = ' '.join(args)
                    if "@" in str_args:
                        banuser = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user.lower() == banuser:
                                user_id = tg_id
                                print(banuser + " banned from " + update.message.chat.title)
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name!")
                        if chat_idstr not in banbase.keys():
                            banbase[chat_idstr] = []
                        if user_id:
                            if owner_admin_mod_check(bot, chat_id, chat_idstr, user_id) != "true":
                                banuser = str_args.replace("@", "")
                                bot.kickChatMember(chat_id, user_id)
                                banbase[chat_idstr] = banbase[chat_idstr] + [user_id]
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="User @" + banuser + " banned from " + update.message.chat.title + " :(")
                            else:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="You can't ban mods! &$%^# ")

                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can ban someone with /ban @username")
                    dumpjson("banbase.json", banbase)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")


def kick_user(bot, update, args):
    if bot.id in get_admin_ids(bot, update.message.chat_id):
        chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
        moderated = loadjson('./moderated.json', "moderated.json")
        if chat_idstr in moderated:
            if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                global idbase
                idbase = loadjson('./idbase.json', "idbase.json")
                str_args = ' '.join(args)
                if "@" in str_args:
                    banuser = str_args.replace("@", "").lower()
                    for tg_id, tg_user in idbase.items():
                        if tg_user == banuser:
                            user_id = tg_id
                    try:
                        user_id
                    except NameError:
                        user_id = ""
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="I don't know anyone by that name!")
                    if user_id:
                        if owner_admin_mod_check(bot, chat_id, chat_idstr, user_id) != "true":
                            banuser = str_args.replace("@", "")
                            bot.kickChatMember(chat_id, user_id)
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="User @" + banuser + " removed from " + update.message.chat.title + " :(")
                        else:
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="You can't kick mods! &$%^# ")
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="You can kick someone with /kick @username")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="Only mods can do stuff like that!")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="I'm not an admin! Please make me one, otherwise I can't do anything!")

def note(bot, update, args):
    global notes
    notes = loadjson('./notes.json', "notes.json")
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
    try:
        notes
    except NameError:
        notes = {}
    try:
        notes[chat_idstr]
    except KeyError:
        notes[chat_idstr] = {}
    try:
        notes[chat_idstr]["admin"]
    except KeyError:
        notes[chat_idstr]["admin"] = {}

    if len(args) == 0:
        try:
            notes[chat_idstr]
        except KeyError:
            note = "No notes for this chat"
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=note)
            return
        for i in notes[chat_idstr]:
            try:
                note
            except NameError:
                note = "Here's a list of notes I have:\n"
            note = note + i + "\n"

        note = note.replace("admin", "")

        for i in notes[chat_idstr]["admin"]:
            try:
                adminnote
            except NameError:
                adminnote = "Locked notes:\n"
            adminnote = adminnote + i + "\n"
        try:
            adminnote
            note = note + adminnote
        except NameError:
            note = note
        note = "".join([s for s in note.strip().splitlines(True) if note.strip()])
    if len(args) == 1:
        notename = args[0]
        commands = ["clearall", "clearlock"]
        if notename in commands:
            if notename == "clearall":
                if update.message.chat.type != "private":
                    if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                        saveme = notes[chat_idstr]["admin"]
                        del notes[chat_idstr]
                        notes[chat_idstr] = {}
                        notes[chat_idstr]["admin"] = {}
                        notes[chat_idstr]["admin"] = saveme
                        dumpjson("notes.json", notes)
                        note = "Notes cleared for " + update.message.chat.title
                    else:
                        note = "clearall is for mods only! `-`"
                else:
                    del notes[chat_idstr]
                    note = "Notes cleared for this chat"

            if notename == "clearlock":
                if update.message.chat.type != "private":
                    if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                        del notes[chat_idstr]["admin"]
                        note = "Locked notes cleared for this chat"
                    else:
                        note = "clearlock is ESPECIALLY for mods only! ~_~"
                else:
                    note = "clearlock only for groups"
        else:
            if notename != "lock":
                if notename in notes[chat_idstr]:
                    note = notename + ":\n" + str(notes[chat_idstr][notename])
                else:
                    if notename in notes[chat_idstr]["admin"]:
                        note = notename + ":\n" + str(notes[chat_idstr]["admin"][notename])
                    else:
                        note = "That note name doesn't exist yet! You can create it with\n/note <code>" + notename + "</code> + <code>content</code>"

            else:
                note = "Use /note lock <code>notename</code> + <code>content</code> to lock a note with that content as editable to only admins."
    if len(args) > 1:
        origargs = args
        notename = args[0]
        del args[0]
        str_args = ' '.join(args)
        commands = ["clear", "lock", "unlock", "clearlock", "clearall" ]
        if notename in commands:
            command = notename

            if notename == "clear":
                if update.message.chat.type != "private":
                    notename = args[0]

                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:
                        if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                            if notename in notes[chat_idstr]["admin"]:
                                del notes[chat_idstr]["admin"][notename]
                                note = "Cleared the note " + notename
                            else:
                                if notename in notes[chat_idstr]:
                                    del notes[chat_idstr][notename]
                                    note = "Cleared the note " + notename
                                else:
                                    note = "The note <code>" + notename + "</code> doesn't exist."
                        else:
                            note = "Only mods can clear notes `-`!"
                else:
                    notename = args[0]
                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:
                        if notename in notes[chat_idstr]:
                            del notes[chat_idstr][notename]
                            note = "Cleared the note " + notename
                        else:
                            note = "The note <code>" + notename + "</code> doesn't exist."

            if notename == "lock":
                if update.message.chat.type != "private":
                    notename = args[0]

                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:
                        if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                            lockednote = args[0]
                            del args[0]
                            str_args = ' '.join(args)
                            if lockednote in notes[chat_idstr]:
                                peasant_paper = notes[chat_idstr][lockednote]
                                del notes[chat_idstr][lockednote]
                            if lockednote in notes[chat_idstr]["admin"]:
                                note = lockednote + " is already locked"
                            else:
                                try:
                                    notes[chat_idstr]["admin"][lockednote] = peasant_paper + str_args
                                    note = lockednote + " has been locked. Any note for regular users with the same name has been deleted."
                                except NameError:
                                    notes[chat_idstr]["admin"][lockednote] = str_args
                                    note = lockednote + " has been locked. Any note for regular users with the same name has been deleted."
                        else:
                            note = "Only mods can create locked notes or lock existing notes! `-`"
                else:
                    note = "locking notes is only for groups"
            if notename == "unlock":
                if update.message.chat.type != "private":
                    notename = args[0]

                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:
                        if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                            lockednote = args[0]
                            del args[0]
                            if lockednote in notes[chat_idstr]:
                                note = lockednote + " is already unlocked"
                            else:
                                if lockednote in notes[chat_idstr]["admin"]:
                                    peasant_paper = notes[chat_idstr]["admin"][lockednote]
                                    del notes[chat_idstr]["admin"][lockednote]
                                    notes[chat_idstr][lockednote] = peasant_paper
                                    note = lockednote + " has been unlocked."
                                else:
                                    note = lockednote + " is not a locked note"
                        else:
                            note = "Only mods can unlock notes! `-`"
                else:
                    note = "unlocking notes is only for groups"
            if notename == "clearlock":
                    note = "Notes can't be command names"
            if notename == "clearall":
                    note = "Notes can't be command names"
        else:
            if notename in notes[chat_idstr]["admin"]:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    notes[chat_idstr]["admin"][notename] = notes[chat_idstr]["admin"][notename] = notes[chat_idstr]["admin"][notename] + "\n" + str_args
                    note = str_args + " added to note " + notename
                else:
                    note = "<code> " + notename + "</code> is locked. Only mods can edit this note! '_'"
            else:
                try:
                    notes[chat_idstr][notename] = notes[chat_idstr][notename] + "\n" + str_args
                    note = str_args + " added to note <code>" + notename + "</code>"
                except KeyError:
                    notes[chat_idstr][notename] = str_args
                    note = str_args + " added to note " + notename
    try:
        note
    except NameError:
        note = "something went wrong"
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=note,
                    parse_mode="HTML")
    dumpjson("notes.json", notes)

def time_command(bot, update, args):
    str_args = ' '.join(args)
    latitude, longitude = latlong(str_args)
    timestamp = time.time()
    if latitude != "fail" and longitude != "fail":
        api_response = requests.get('https://maps.googleapis.com/maps/api/timezone/json?location={0},{1}&timestamp={2}'.format(latitude,longitude,timestamp))
        api_response_dict = api_response.json()

        if api_response_dict['status'] == 'OK':
            timezone_id = api_response_dict['timeZoneId']
            dt_timezone = timezone(timezone_id)
            dt_time = datetime.now(dt_timezone)
            dt_time = "The local time in " + str(dt_timezone) + " is: " + dt_time.strftime("%A, %d %B - %H:%M:%S")
            dt_time = dt_time.replace("_", " ")
        if api_response_dict['status'] == 'ZERO_RESULTS':
            dt_time = "It seems that in " + str_args + " they do not have a concept of time"
    else:
        dt_time = "It seems that in " + '"' + str_args + '"' + " they do not have a concept of time"
    try:
        dt_time
    except NameError:
        dt_time = "something went wrong"
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=dt_time)
    print(dt_time)
    return(dt_time)

def save_message(bot, update, args):
    global saved
    saved = loadjson('./saved.json', "saved.json")
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
    if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
        try:
            saved
        except NameError:
            saved = {}
        if chat_idstr not in saved.keys():
            saved[chat_idstr] = {}

        if len(args) == 0:
            saves = "Save a message with\n/save <code>name</code> + <code>message</code>\nand retrieve it later with\n/get <code>name</code>"
        if len(args) == 1:
            saves = "Save a message with\n/save <code>name</code> + <code>message</code>\nand retrieve it later with\n/get <code>name</code>"
            savename = args[0]
            if savename in saved[chat_idstr]:
                saves = savename + ":\n" + str(saved[chat_idstr][savename])
            else:
                saves = "That name isn't saved yet! You can create it with\n/save <code>" + savename + "</code> + <code>message</code>"
        if len(args) > 1:
            message_text = update.message.text
            savename = args[0]
            message_text = message_text.split(' ', 2)[2]
            saved[chat_idstr][savename] = message_text
            saves = "Saved " + savename
        try:
            saves
        except NameError:
            saves = "something went wrong"
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=saves,
                        parse_mode="HTML")
        dumpjson("saved.json", saved)
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Only for mods bruh")

def get_message(bot, update, args):
    global saved
    saved = loadjson('./saved.json', "saved.json")
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)


    if len(args) == 0:
        getme = "Get a saved message with\n/get <code>name</code>"
    if len(args) == 1:
        savename = args[0]
        if savename in saved[chat_idstr]:
            getme = savename + ":\n" + str(saved[chat_idstr][savename])
        else:
            getme = "That name isn't saved yet! You can create it with\n/save <code>" + savename + "</code> + <code>message</code>"
    if len(args) > 1:
        getme = "Only try to retrieve one saved message at a time!\nGet a saved message with\n/get <code>name</code>"

    try:
        getme
    except NameError:
        getme = "something went wrong"
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=getme,
                    parse_mode="HTML")

def lockme(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            global locked
            lockedmsg = ""
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    locked = loadjson('./locked.json', "locked.json")
                    if chat_idstr not in locked.keys():
                        locked[chat_idstr] = {}
                        locked[chat_idstr]["sticker"] = "no"
                        locked[chat_idstr]["gif"] = "no"
                        locked[chat_idstr]["flood"] = "no"
                        locked[chat_idstr]["arabic"] = "yes"
                        locked[chat_idstr]["NSFW"] = "off"

                    if len(args) > 0:
                        if args[0] == "sticker":
                            if locked[chat_idstr]["sticker"] != "yes":
                                locked[chat_idstr]["sticker"] = "yes"
                                lockedmsg = "Stickers are now locked"
                            else:
                                lockedmsg = "Stickers are already locked"
                        if args[0] == "flood":
                            if locked[chat_idstr]["flood"] != "yes":
                                locked[chat_idstr]["flood"] = "yes"
                                lockedmsg = "Flooding is now locked"
                            else:
                                lockedmsg = "Flooding is already locked"
                        if args[0] == "arabic" or args[0] == "Arabic":
                            if locked[chat_idstr]["arabic"] != "yes":
                                locked[chat_idstr]["arabic"] = "yes"
                                lockedmsg = "Arabic is now locked"
                            else:
                                lockedmsg = "Arabic is already locked"
                        if args[0] == "gif":
                            if locked[chat_idstr]["gif"] != "yes":
                                locked[chat_idstr]["gif"] = "yes"
                                lockedmsg = "Gif's are now locked"
                            else:
                                lockedmsg = "Gif's are already locked"
                    else:
                        lockedmsg = "/lock <code>setting</code>, not just /lock"
                    if len(args) > 1:
                        lockedmsg = "Please only lock one setting at a time. Don't go power crazy"
                    if lockedmsg:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text=lockedmsg,
                                        parse_mode="HMTL")
                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="Something went wrong.")
                    dumpjson("locked.json", locked)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Locking settings is for groups!")

def fixlocked(bot, update):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            global locked
            lockedmsg = ""
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    locked = loadjson('./locked.json', "locked.json")
                    if chat_idstr not in locked.keys():
                        locked[chat_idstr] = {}
                        locked[chat_idstr]["sticker"] = "no"
                        locked[chat_idstr]["gif"] = "no"
                        locked[chat_idstr]["flood"] = "yes"
                        locked[chat_idstr]["arabic"] = "yes"
                        locked[chat_idstr]["NSFW"] = "off"
                    locked[chat_idstr]["flood"] = "yes"
                    flooding = loadjson('./flooding.json', "flooding.json")
                    flooding[chat_idstr] = {}
                    flooding[chat_idstr]["limit"] = 10
                    flooding[chat_idstr]["floodcount"] = 1
                    dumpjson("flooding.json", flooding)
                    dumpjson("locked.json", locked)

def unlockme(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    global locked
                    lockedmsg = ""
                    locked = loadjson('./locked.json', "locked.json")
                    if chat_idstr not in locked.keys():
                        locked[chat_idstr] = {}
                        locked[chat_idstr]["sticker"] = "no"
                        locked[chat_idstr]["gif"] = "no"
                        locked[chat_idstr]["flood"] = "no"
                        locked[chat_idstr]["arabic"] = "yes"
                        locked[chat_idstr]["NSFW"] = "off"

                    if len(args) > 0:
                        if args[0] == "sticker":
                            if locked[chat_idstr]["sticker"] != "no":
                                locked[chat_idstr]["sticker"] = "no"
                                lockedmsg = "Stickers are now unlocked"
                            else:
                                lockedmsg = "Stickers are already unlocked"
                        if args[0] == "flood":
                            if locked[chat_idstr]["flood"] != "no":
                                locked[chat_idstr]["flood"] = "no"
                                lockedmsg = "Flooding is now unlocked"
                            else:
                                lockedmsg = "Flooding is already unlocked"
                        if args[0] == "arabic" or args[0] == "Arabic":
                            if locked[chat_idstr]["arabic"] != "no":
                                locked[chat_idstr]["arabic"] = "no"
                                lockedmsg = "Arabic is now unlocked"
                            else:
                                lockedmsg = "Arabic is already unlocked"
                        if args[0] == "gif":
                            if locked[chat_idstr]["gif"] != "no":
                                locked[chat_idstr]["gif"] = "no"
                                lockedmsg = "Gif's are now unlocked"
                            else:
                                lockedmsg = "Gif's are already unlocked"
                    else:
                        lockedmsg = "/unlock <code>setting</code>, not just /unlock"
                    if len(args) > 1:
                        lockedmsg = "Please only unlock one setting at a time. Don't give them too much freedom"
                    if lockedmsg:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text=lockedmsg,
                                        parse_mode="HTML")
                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="Something went wrong.")
                    dumpjson("locked.json", locked)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Unlocking settings is for groups!")

def setflood(bot, update, args):
    if update.message.chat.type != "private":

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            moderated = loadjson('./moderated.json', "moderated.json")
            promoted = loadjson('./promoted.json', "promoted.json")

            if chat_idstr in moderated:

                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    flooding = loadjson('./flooding.json', "flooding.json")
                    intarg = int(args[0])
                    if isinstance(intarg, int):
                        if intarg <= 10 and intarg >=5:
                            flooding[chat_idstr]["limit"] = intarg
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="Flood has been set to: " + str(intarg))
                            dumpjson("flooding.json", flooding)
                        else:
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="The flood limit must be a number ≥ 5 and ≤ 10")
                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="The flood limit must be a number ≥ 5 and ≤ 10")
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="I don't mind if you flood me! I only care about flooding in groups.")


def checknsfw(bot, update, args):
    if update.message.chat.type != "private":
        chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
        moderated = loadjson('./moderated.json', "moderated.json")
        promoted = loadjson('./promoted.json', "promoted.json")
        if chat_idstr in moderated:
            if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                locked = loadjson('./locked.json', "locked.json")
                if chat_idstr not in locked.keys():
                    locked[chat_idstr] = {}
                    locked[chat_idstr]["sticker"] = "no"
                    locked[chat_idstr]["gif"] = "no"
                    locked[chat_idstr]["flood"] = "no"
                    locked[chat_idstr]["arabic"] = "yes"
                    locked[chat_idstr]["NSFW"] = "off"
                str_args = args[0]
                if args[0]:
                    if args[0] == "on":
                        if locked[chat_idstr]["NSFW"] != "on":
                            locked[chat_idstr]["NSFW"] = "on"
                            dumpjson('locked.json', locked)
                            message = "NSFW turned on"
                        else:
                            message = "NSFW already on"
                    if args[0] == "off":
                        if locked[chat_idstr]["NSFW"] != "off":
                            locked[chat_idstr]["NSFW"] = "off"
                            dumpjson('locked.json', locked)
                            message = "NSFW turned off"
                        else:
                            message = "NSFW already off"
                else:
                    message = "Usage: /nsfw [on/off]"
            else:
                message = "You're not an admin."

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=message)



def getbutts(bot, update):
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)

    locked = loadjson('./locked.json', "locked.json")
    if locked[chat_idstr]["NSFW"] == "on":

        url = getRandomButts(1)
        os.makedirs('butts/', exist_ok=True)
        filename = url.strip().split('/')[-1]
        mypath = "butts"
        fullfilename = os.path.join(mypath, filename)
        urllib.request.urlretrieve(url, fullfilename)

        bot.sendPhoto(
            photo=open(fullfilename, 'rb'),
            chat_id=update.message.chat_id)

def getboobs(bot, update):
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)

    locked = loadjson('./locked.json', "locked.json")
    if locked[chat_idstr]["NSFW"] == "on":

        url = getRandomBoobs(1)
        os.makedirs('boobs/', exist_ok=True)
        filename = url.strip().split('/')[-1]
        mypath = "boobs"
        fullfilename = os.path.join(mypath, filename)
        urllib.request.urlretrieve(url, fullfilename)

        bot.sendPhoto(
            photo=open(fullfilename, 'rb'),
            chat_id=update.message.chat_id)

def resetwarn(bot, update, args):
    if update.message.chat.type != "private":
        moderated = loadjson('./moderated.json', "moderated.json")
        sentlock = loadjson('./sentlock.json', "sentlock.json")
        idbase = loadjson('./idbase.json', "idbase.json")

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            if chat_idstr in moderated:
                if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                    str_args = ' '.join(args)
                    if "@" in str_args:
                        unwarn = str_args.replace("@", "").lower()
                        for tg_id, tg_user in idbase.items():
                            if tg_user == unwarn:
                                user_id = tg_id
                        try:
                            user_id
                        except NameError:
                            user_id = ""
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="I don't know anyone by that name!")
                        unwarnuser = str_args.replace("@", "")
                        if chat_idstr in sentlock.keys():
                            if user_id in sentlock[chat_idstr].keys():
                                del sentlock[chat_idstr][user_id]
                                dumpjson("sentlock.json", sentlock)
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="@" + unwarnuser + " 's warns are reset")
                            else:
                                bot.sendMessage(chat_id=update.message.chat_id,
                                                text="@" + unwarnuser + " has no warnings")
                        else:
                            bot.sendMessage(chat_id=update.message.chat_id,
                                            text="@" + unwarnuser + " has no warnings")
                    else:
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text="You can reset someone's warn counter with /reset @username")
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text="Only mods can do stuff like that!")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You don't have any warns but okay? Your warns are 'reset' Mr. I like to spam the bot in private chat")
def rules_get(bot, update):
    if update.message.chat.type != "private":
        moderated = loadjson('./moderated.json', "moderated.json")

        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            if chat_idstr in moderated:
                rules = loadjson('./rules.json', "rules.json")
                chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
                if chat_idstr in rules.keys():
                    msg = update.message.chat.title + " <b>Rules:</b>\n" + rules[chat_idstr]
                else:
                    msg = "I don't have any rules for " + update.message.chat.title + "!\nMaybe you need to set them with /setrules"
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=msg)

            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="No rules for private chat!")
def setrules(bot, update, args):
    global rules
    moderated = loadjson('./moderated.json', "moderated.json")
    if update.message.chat.type != "private":
        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            if chat_idstr in moderated:
                rules = loadjson('./rules.json', "rules.json")

                if len(args) == 0:
                    msg = "Set the rules with\n/setrules <code>rules</code>\nand retrieve it later with\n/rules"
                if len(args) >= 1:
                    message_text = update.message.text
                    rules_txt = message_text.split(' ', 1)[1]
                    rules[chat_idstr] = rules_txt
                    msg =  "Ok, I've set the rules for this chat! Get them with\n/rules"
                try:
                    msg
                except NameError:
                    msg = "something went wrong"
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=msg)
                dumpjson("rules.json", rules)
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="No rules for private chat!")

def settings(bot, update):
    moderated = loadjson('./moderated.json', "moderated.json")
    chat_idstr = str(update.message.chat_id)
    locked = loadjson('./locked.json', "locked.json")
    if chat_idstr not in locked.keys():
        fixlocked(bot, update)
        time.sleep(1)
    if chat_idstr in moderated:
        locked = loadjson('./locked.json', "locked.json")
        flooding = loadjson('./flooding.json', "flooding.json")
        if locked[chat_idstr]["sticker"] == "yes":
            sticker = "Lock Sticker:  <code>Yes</code>\n"
        else:
            sticker = "Lock Sticker:  <code>No</code>\n"
        if locked[chat_idstr]["gif"] == "yes":
            gif = "Lock Gif:  <code>Yes</code>\n"
        else:
            gif = "Lock Gif:  <code>No</code>\n"
        if locked[chat_idstr]["flood"] == "yes":
            if "limit" not in flooding[chat_idstr].keys():
                fixlocked(bot, update)
                flooding = loadjson('./flooding.json', "flooding.json")
            limit = flooding[chat_idstr]["limit"]
            flood = "Lock flood:  <code>Yes</code>\nFlood sensitivity: " + str(limit) + "\n"
        else:
            flood = "Lock flood:  <code>No</code>\n"
        if locked[chat_idstr]["arabic"] == "yes":
            arabic = "Lock Arabic:  <code>Yes</code>\n"
        else:
            arabic = "Lock Arabic:  <code>No</code>\n"
        if locked[chat_idstr]["NSFW"] == "on":
            nsfw = "NSFW:  <code>Yes</code>\n"
        else:
            nsfw = ""
        if nsfw:
            message = "Supergroup settings:\n" + sticker + gif + flood + arabic + nsfw
        else:
            message = "Supergroup settings:\n" + sticker + gif + flood + arabic
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=message,
                        parse_mode="HTML")

def welcomeme(bot, update, args):
    global welcome
    welcome = loadjson('./welcome.json', "welcome.json")
    moderated = loadjson('./moderated.json', "moderated.json")
    global asker_chatidstr
    global asker
    chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
    asker = fromid
    asker_chatidstr = chat_idstr
    if update.message.chat.type != "private":
        if bot.id in get_admin_ids(bot, update.message.chat_id):
            chat_idstr, chat_id, fromid, fromidstr = common_vars(bot, update)
            if owner_admin_mod_check(bot, chat_id, chat_idstr, fromidstr) == "true":
                if chat_idstr in moderated:
                    if chat_idstr not in welcome.keys():
                        welcome[chat_idstr] = {}
                        welcome[chat_idstr]["welcome"] = ""
                        welcome[chat_idstr]["message"] = ""
                        dumpjson("welcome.json", welcome)

                    if len(args) == 0:
                        keyboard = [[InlineKeyboardButton("YES", callback_data='welcomeon')],

                        [InlineKeyboardButton("NO", callback_data='welcomeoff')]]

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        update.message.reply_text('Should I welcome new visitors?', reply_markup=reply_markup)
                    else:
                        message_text = update.message.text
                        welcome_txt = message_text.split(' ', 1)[1]
                        welcome[chat_idstr]["message"] = welcome_txt
                        msg =  "Alright, I've updated my mannerisms!"
                        dumpjson("welcome.json", welcome)
                        bot.sendMessage(chat_id=update.message.chat_id,
                                        text=msg)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=update.message.chat.title + "? Never heard of it! Tell me about it with /add")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="Only mods can do stuff like that!")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I'm not an admin! Please make me one, otherwise I can't do anything!")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Nope. Not welcoming you.")

def idme(bot, update, args):
    idbase = loadjson('./idbase.json', "idbase.json")

    str_args = ' '.join(args)
    if "@" in str_args:
        idme_ = str_args.replace("@", "").lower()
        for tg_id, tg_user in idbase.items():
            if tg_user.lower() == idme_:
                print(tg_user)
                user_id = tg_id
        try:
            user_id
        except NameError:
            user_id = ""
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I don't know anyone by that name! If I'm not admin of a group they're in, or they haven't said anything, that could be why!")
        if user_id:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="The Telegram ID of " + "@" + idme_ + " is " + user_id)
    else:
        if update.message.chat.type != "private":
            if str_args == "":
                chat_idstr = str(update.message.chat_id)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="The ID of " + update.message.chat.title + " is " + chat_idstr)



def button(bot, update, direct=True):
        global welcome
        welcome = loadjson('./welcome.json', "welcome.json")
        user_id = update.callback_query.from_user.id
        if user_id == asker:
            query = update.callback_query
            chat_idstr = asker_chatidstr
            selected_button = query.data
            if selected_button == 'welcomeon':
                bot.editMessageText(text="Selected option: <b>YES</b>",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    parse_mode="HTML")
                if not welcome[chat_idstr]["welcome"]:
                    welcome[chat_idstr]["welcome"] = "yes"
                    bot.sendMessage(chat_id=query.message.chat_id,
                                    text="I'll welcome new users from now on!",
                                    parse_mode="Markdown")
                    dumpjson("welcome.json", welcome)
                else:
                    bot.sendMessage(chat_id=query.message.chat_id,
                                    text="I already know how to be polite! :)",
                                    parse_mode="Markdown")
                    dumpjson("welcome.json", welcome)

            if selected_button == 'welcomeoff':
                bot.editMessageText(text="Selected option: <b>NO</b>",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id,
                                    parse_mode="HTML")
                if welcome[chat_idstr]["welcome"]:
                    del welcome[chat_idstr]["welcome"]
                    bot.sendMessage(chat_id=query.message.chat_id,
                                    text="Well...I was gonna be polite, but I guess not.",
                                    parse_mode="Markdown")
                else:
                    bot.sendMessage(chat_id=query.message.chat_id,
                                    text="I don't welcome people. Yeah. I got it.",
                                    parse_mode="Markdown")
        else:
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="You trying to spam me bro?",
                                parse_mode="Markdown")
        return False

start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help_message, pass_args=True)
note_handler = CommandHandler('note', note, pass_args=True)
time_handler = CommandHandler('time', time_command, pass_args=True)
ban_handler = CommandHandler('ban', banme, pass_args=True)
banall_handler = CommandHandler('banall', banall, pass_args=True)
unban_handler = CommandHandler('unban', unbanme, pass_args=True)
unbanall_handler = CommandHandler('unbanall', unbanall, pass_args=True)
add_handler = CommandHandler('add', add)
rem_handler = CommandHandler('rem', rem)
kick_handler = CommandHandler('kick', kick_user, pass_args=True)
promote_handler = CommandHandler('promote', promoteme, pass_args=True)
demote_handler = CommandHandler('demote', demoteme, pass_args=True)
modlist_handler = CommandHandler('modlist', modlist)
save_handler = CommandHandler('save', save_message, pass_args=True)
get_handler = CommandHandler('get', get_message, pass_args=True)
lock_handler = CommandHandler('lock', lockme, pass_args=True)
unlock_handler = CommandHandler('unlock', unlockme, pass_args=True)
settings_handler = CommandHandler('settings', settings)
setflood_handler = CommandHandler('setflood', setflood, pass_args=True)
id_handler = CommandHandler('id', idme, pass_args=True)
butts_handler = CommandHandler('butts', getbutts)
boobs_handler = CommandHandler('boobs', getboobs)
nsfw_handler = CommandHandler('nsfw', checknsfw, pass_args=True)
setrules_handler = CommandHandler('setrules', setrules, pass_args=True)
rules_handler = CommandHandler('rules', rules_get)
banlist_handler = CommandHandler('banlist', getbanlist)
gbanlist_handler = CommandHandler('gbanlist', getglobalbanlist)
resetwarn_handler = CommandHandler('reset', resetwarn, pass_args=True)
welcome_handler = CommandHandler('welcome', welcomeme, pass_args=True)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(note_handler)
dispatcher.add_handler(time_handler)
dispatcher.add_handler(ban_handler)
dispatcher.add_handler(banall_handler)
dispatcher.add_handler(unban_handler)
dispatcher.add_handler(unbanall_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(rem_handler)
dispatcher.add_handler(kick_handler)
dispatcher.add_handler(promote_handler)
dispatcher.add_handler(demote_handler)
dispatcher.add_handler(modlist_handler)
dispatcher.add_handler(save_handler)
dispatcher.add_handler(get_handler)
dispatcher.add_handler(lock_handler)
dispatcher.add_handler(unlock_handler)
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(setflood_handler)
dispatcher.add_handler(id_handler)
dispatcher.add_handler(butts_handler)
dispatcher.add_handler(boobs_handler)
dispatcher.add_handler(nsfw_handler)
dispatcher.add_handler(setrules_handler)
dispatcher.add_handler(rules_handler)
dispatcher.add_handler(banlist_handler)
dispatcher.add_handler(gbanlist_handler)
dispatcher.add_handler(resetwarn_handler)
dispatcher.add_handler(welcome_handler)


dispatcher.add_handler(MessageHandler([Filters.all], receiveMessage))
dispatcher.add_handler(MessageHandler([Filters.all], receiveLocked))
dispatcher.add_handler(MessageHandler([Filters.all], floodcheck))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()

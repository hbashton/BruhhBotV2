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
from pytz import timezone
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, Chat, User, Message, Update, ChatMember, UserProfilePhotos, File, ReplyMarkup, TelegramObject
from urllib.request import urlopen
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
jenkins = config['JENKINS']['url']
user = config['JENKINS']['user']
password = config['JENKINS']['password']
token = config['JENKINS']['token']
job = config['JENKINS']['job']
gerrituser = config['GERRIT']['user']
gerriturl = config['GERRIT']['url']
protocol = config['GERRIT']['protocol']
jenkinsconfig = config['JENKINS']['on']
myusername = config['ADMIN']['username']

dispatcher = updater.dispatcher


hereyago = "Here's a list of commands for you to use:\n"
build_help = "/build to start the build process\n"
changelog_help = "/changelog 'text' to set the changelog\n"
sync_help = "/sync to set sync to on/off\n"
clean_help = "/clean to set clean to on/off\n"
repopick_a_help = "/repopick to set repopick on or off\n"
repopick_b_help = "-- /repopick `changes` to pick from gerrit on build\n"
open_a_help = "/open to see all open changes\n"
open_b_help = "-- /open `projects` to see open changes for certain projects\n"
pickopen_help = "/pickopen to pick all open changes on gerrit\n"
note_a_help = "/note 'notename' to see the contents of a note\n"
note_b_help = "-- /note 'notename' 'contents' to set the contents of a note\n"
note_c_help = "-- /note lock 'notename' to lock a note (admins only)\n"
note_d_help = "-- /note unlock 'notename' to unlock a note (admins only)\n"
note_e_help = "-- /note clear 'notename' to clear a note (admins only)\n"
note_f_help = "-- /note clearall to clear all normal notes (admins only)\n"
note_g_help = "-- /note clearlock to clear all locked notes (admins only)\n"
help_help = "/help to see this message\n--/help 'command' to see information about that command :)" # love this lmao help_help

jenkinsnotmaster = "Sup *not* master. \n" + hereyago + open_a_help + open_b_help + note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help + help_help
nojenkinsnotmaster = "Sup *not* master. \n" + hereyago + open_a_help + open_b_help + note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help + help_help
jenkinsmaster = "Sup" + myusername + "\n" + hereyago + build_help + changelog_help + sync_help + clean_help + repopick_a_help + repopick_b_help + pickopen_help + open_a_help + open_b_help + note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help + help_help
nojenkinsmaster = "Sup" + myusername + "\n" + hereyago + open_a_help + open_b_help + note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help + help_help

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
    
def get_user_info(bot, chat_id, user_id, find):
    return bot.getChatMember(chat_id, user_id)["user"][find]

def get_chat_info(bot, chat_id):
    return bot.getChat(chat_id)
    
def receiveMessage(bot, update):
    tguser = str(update.message.from_user.username)
    tgid = str(update.message.from_user.id)
    chat_idstr = str(update.message.chat_id)

    global idbase
    
    PATH='./idbase.json'
    
    if not os.path.isfile(PATH) or not os.access(PATH, os.R_OK):
        print ("Either file is missing or is not readable. Creating.")
        idbase = {}
        with open("idbase.json", 'w') as f:
            json.dump(idbase, f)
    with open("idbase.json") as f:
        idbase = json.load(f)
    if chat_idstr not in idbase:
        idbase[chat_idstr] = {}
    if tgid not in idbase[chat_idstr].keys():
        idbase[chat_idstr][tgid] = tguser
        
    if update.message.new_chat_member:
        tguser = str(update.message.new_chat_member["username"])
        tgid = str(update.message.new_chat_member["id"])
        if chat_idstr not in idbase:
            idbase[chat_idstr] = {}
        if tgid not in idbase[chat_idstr].keys():
            idbase[chat_idstr][tgid] = tguser
            
    if update.message.left_chat_member:
        tguser = str(update.message.left_chat_member["username"])
        tgid = str(update.message.left_chat_member["id"])
        if chat_idstr not in idbase:
            idbase[chat_idstr] = {}
        if tgid not in idbase[chat_idstr].keys():
            idbase[chat_idstr][tgid] = tguser

    with open("idbase.json", 'w') as f:
        json.dump(idbase, f)

def kick_user(bot, update, args):
    chat_id = update.message.chat_id
    chat_idstr = str(update.message.chat_id)
    global idbase
    with open("idbase.json") as f:
        idbase = json.load(f)
        
    str_args = ' '.join(args)
    if "@" in str_args:
        banuser = str_args.replace("@", "")
        for tg_id, tg_user in idbase[chat_idstr].items():
            if tg_user == banuser:
                user_id = tg_id
        if not user_id:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="I don't know anyone by that name!")
        else:
            bot.kickChatMember(chat_id, user_id)
            
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="User @" + banuser + " removed from " + update.message.chat.title + " :(")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You can kick someone with /kick @username")
    with open("idbase.json", 'w') as f:
        json.dump(idbase, f)

# bot functions
def start(bot, update):
    if update.message.chat.type == "private":

        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Hi. I'm Hunter's Jenkins Bot! You can use me to do lots of cool stuff, assuming your name is @hunter_bruhh! If not, then I'm not much use to you right now! Maybe he'll implement some cool stuff later!")
        if update.message.from_user.id != int(config['ADMIN']['id']):
            if jenkinsconfig == "yes":
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=jenkinsnotmaster)
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
            else:
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=nojenkinsnotmaster)
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
        else:
            if jenkinsconfig == "yes":
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=jenkinsmaster)
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=nojenkinsmaster)
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)

def help_message(bot, update, args):
    jenkinsmasterlist = ["build", "changelog", "sync", "clean", "repopick", "pickopen", "open", "note"]
    nojenkinsmasterlist = ["open", "note"]
    nojenkinslist = ["open", "note"]
    jenkinslist = ["open", "note"]
    args_length = len(args)
    if update.message.from_user.id != int(config['ADMIN']['id']):
        if jenkinsconfig == "yes":
            if args_length != 0:
                if args_length > 1:
                    for x in jenkinslist:
                        try:
                            helpme
                        except NameError:
                            helpmeplox = "Please use only one argument. A list of arguments aka commands to ask about would be:\n"
                    helpmeplox = helpmeplox + x + ",\n"
                    helpme = helpmeplox
                else:
                    if args[0] in jenkinslist:
                        if args[0] == "open":
                            helpme = open_a_help + open_b_help
                        if args[0] == "note":
                            helpme = note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help
                    else:
                        helpme = "That's not a command to ask about."
                bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=helpme)
            else:
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=jenkinsnotmaster)
        else:
            if args_length != 0:
                if args_length > 1:
                    for x in nojenkinslist:
                        try:
                            helpme
                        except NameError:
                            helpmeplox = "Please use only one argument. A list of arguments aka commands to ask about would be:\n"
                    helpmeplox = helpmeplox + x + ",\n"
                    helpme = helpmeplox
                else:
                    if args[0] in nojenkinslist:
                        if args[0] == "open":
                            helpme = open_a_help + open_b_help
                        if args[0] == "note":
                            helpme = note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help
                    else:
                        helpme = "That's not a command to ask about."
                bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=helpme)
                bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=helpme)
            else:
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=nojenkinsnotmaster)
    else:
        if jenkinsconfig == "yes":
            if args_length != 0:
                if args_length > 1:
                    for x in jenkinsmasterlist:
                        try:
                            helpme
                        except NameError:
                            helpmeplox = "Please use only one argument. A list of arguments aka commands to ask about would be:\n"
                    helpmeplox = helpmeplox + x + ",\n"
                    helpme = helpmeplox
                else:
                    if args[0] in jenkinsmasterlist:
                        if args[0] == "build":
                            helpme = build_help
                        if args[0] == "changelog":
                            helpme = changelog_help
                        if args[0] == "sync":
                            helpme = sync_help
                        if args[0] == "clean":
                            helpme = clean_help
                        if args[0] == "repopick":
                            helpme = repopick_a_help + repopick_b_help
                        if args[0] == "pickopen":
                            helpme = pickopen_help
                        if args[0] == "open":
                            helpme = open_a_help + open_b_help
                        if args[0] == "note":
                            helpme = note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help
                    else:
                        helpme = "That's not a command to ask about."
                bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=helpme)
            else:
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=jenkinsmaster)
        else:
            if args_length != 0:
                if args_length > 1:
                    for x in nojenkinsmasterlist:
                        try:
                            helpme
                        except NameError:
                            helpmeplox = "Please use only one argument. A list of arguments aka commands to ask about would be:\n"
                    helpmeplox = helpmeplox + x + ",\n"
                    helpme = helpmeplox
                else:
                    if args[0] in nojenkinsmasterlist:
                        if args[0] == "build":
                            helpme = build_help
                        if args[0] == "changelog":
                            helpme = changelog_help
                        if args[0] == "sync":
                            helpme = sync_help
                        if args[0] == "clean":
                            helpme = clean_help
                        if args[0] == "repopick":
                            helpme = repopick_a_help + repopick_b_help
                        if args[0] == "pickopen":
                            helpme = pickopen_help
                        if args[0] == "open":
                            helpme = open_a_help + open_b_help
                        if args[0] == "note":
                            helpme = note_a_help + note_b_help + note_c_help + note_d_help + note_e_help + note_f_help + note_g_help
                    else:
                        helpme = "That's not a command to ask about."
                bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=helpme)
            else:
                bot.sendChatAction(chat_id=update.message.chat_id,
                                   action=ChatAction.TYPING)
                time.sleep(1)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=nojenkinsmaster)

def link(bot, update, args):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        str_args = ' '.join(args)
        args_length = len(args)
        if str_args == "":
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="You must provide change numbers to get a link to each change\n e.g. /link 99 123 345",
                                parse_mode="Markdown")
        else:
            for i in range(args_length):
                try:
                    link
                except NameError:
                    link = ""
                link = link + args[i] + " - " + protocol + "://" + gerriturl + "/#/c/" + args[i] + "/" + "\n"
            bot.sendMessage(chat_id=update.message.chat_id,
                                text=link)


def openchanges(bot, update, args):

        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        curl = "curl -H 'Accept-Type: application/json' " + protocol + "://" + gerrituser + "@" + gerriturl + "/changes/?q=status:open | sed '1d' > open.json"
        command = subprocess.Popen(curl, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with open('open.json', encoding='utf-8') as data_file:
            data = json.load(data_file)
        dict_length = len(data)
        str_args = ' '.join(args)
        args_length = len(args)
        if str_args != "":
            for i in range(dict_length):
                try:
                    openc
                except NameError:
                    openc = ""
                if str(data[i]['project']) in args:
                    openc = openc + "\n" + "<a href=" + '"' + protocol + "://" + gerriturl + "/#/c/" + str(data[i]['_number']) + "/" + '"' + ">" + str(data[i]['_number']) + "</a>" + " - " + str(data[i]['subject'])
            print(openc)
            for i in range(dict_length):
                try:
                    cnum
                except NameError:
                    cnum = "/repopick"
                if str(data[i]['project']) in args:
                    cnum = cnum + " " + str(data[i]['_number'])
        else:
            for i in range(dict_length):
                try:
                    openc
                except NameError:
                    openc = ""
                openc = openc + "\n" + "<a href=" + '"' + protocol + "://" + gerriturl + "/#/c/" + str(data[i]['_number']) + "/" + '"' + ">" + str(data[i]['_number']) + "</a>" + " - " + str(data[i]['subject'])
            for i in range(dict_length):
                try:
                    cnum
                except NameError:
                    cnum = "/repopick"
                cnum = cnum + " " + str(data[i]['_number'])
        print(openc)
        print(cnum)
        if update.message.from_user.id == int(config['ADMIN']['id']):

            bot.sendMessage(chat_id=update.message.chat_id,
                            text=openc,
                            parse_mode="HTML")
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=cnum,
                            parse_mode="Markdown")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=openc,
                            parse_mode="HTML")

def note(bot, update, args):
    global notes
    PATH='./notes.json'
    if not os.path.isfile(PATH) or not os.access(PATH, os.R_OK):
        print ("Either file is missing or is not readable. Creating.")
        notes = {}
        with open("notes.json", 'w') as f:
            json.dump(notes, f)
    with open("notes.json") as f:
        notes = json.load(f)
    chat_idstr = str(update.message.chat_id)
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
                    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
                        saveme = notes[chat_idstr]["admin"]
                        del notes[chat_idstr]
                        notes[chat_idstr] = {}
                        notes[chat_idstr]["admin"] = {}
                        notes[chat_idstr]["admin"] = saveme
                        with open("notes.json", 'w') as f:
                            json.dump(notes, f)
                        note = "Notes cleared for " + update.message.chat.title
                    else:
                        note = "clearall is for admins only chutiya"
                else:
                    del notes[chat_idstr]
                    note = "Notes cleared for this chat"
                    
            if notename == "clearlock":
                if update.message.chat.type != "private":
                    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
                        del notes[chat_idstr]["admin"]
                        note = "Locked notes cleared for this chat"
                    else:
                        note = "clearlock is ESPECIALLY for admins only chutiya"
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
                        note = "That note name exist yet! You can create it with\n/note " + notename + " 'content'"

            else:
                note = "Use /note lock 'notename' 'content' to lock a note with that content as editable to only admins."
    if len(args) > 1:
        origargs = args
        notename = args[0]
        del args[0]
        str_args = ' '.join(args)
        commands = ["clear", "lock", "unlock" ]
        if notename in commands:
            command = notename

            if notename == "clear":
                if update.message.chat.type != "private":
                    notename = args[0]

                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:
                        if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
                            if notename in notes[chat_idstr]["admin"]:
                                del notes[chat_idstr]["admin"][notename]
                                note = "Cleared the note " + notename
                            else:
                                if notename in notes[chat_idstr]:
                                    del notes[chat_idstr][notename]
                                    note = "Cleared the note " + notename
                                else:
                                    note = notename + " doesn't exist."
                        else:
                            note = "Only admins can clear notes!"
                else:
                    notename = args[0]
                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:
                        if notename in notes[chat_idstr]:
                            del notes[chat_idstr][notename]
                            note = "Cleared the note " + notename
                        else:
                            note = notename + " doesn't exist."
        
            if notename == "lock":
                if update.message.chat.type != "private":
                    notename = args[0]

                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:                    
                        if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
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
                            note = "Only admins can create locked notes or lock existing notes"
                else:
                    note = "locking notes is only for groups"
            if notename == "unlock":
                if update.message.chat.type != "private":
                    notename = args[0]

                    if notename in commands:
                        note = "Notes cannot be command names."
                    else:                    
                        if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
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
                            note = "Only admins can unlock notes"
                else:
                    note = "unlocking notes is only for groups"
        else:
            if notename in notes[chat_idstr]["admin"]:
                if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
                    notes[chat_idstr]["admin"][notename] = notes[chat_idstr]["admin"][notename] = notes[chat_idstr]["admin"][notename] + "\n" + str_args
                    note = str_args + " added to note " + notename
                else:
                    note = notename + " is locked. Only admins can edit this note"
            else:
                try:
                    notes[chat_idstr][notename] = notes[chat_idstr][notename] + "\n" + str_args
                    note = str_args + " added to note " + notename
                except KeyError:
                    notes[chat_idstr][notename] = str_args
                    note = str_args + " added to note " + notename
    try:
        note
    except NameError:
        note = "something went wrong"
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=note)
    with open("notes.json", 'w') as f:
        json.dump(notes, f)

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
    

if jenkinsconfig == "yes":
    def pickopen(bot, update):
        if update.message.from_user.id == int(config['ADMIN']['id']):
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
            curl = "curl -H 'Accept-Type: application/json' " + protocol + "://" + gerrituser + "@" + gerriturl + "/changes/?q=status:open | sed '1d' > open.json"
            command = subprocess.Popen(curl, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            with open('open.json', encoding='utf-8') as data_file:
                data = json.load(data_file)
            dict_length = len(data)
            for i in range(dict_length):
                try:
                    cnumbers
                except NameError:
                    cnumbers = ""
                cnumbers = cnumbers + " " + str(data[i]['_number'])
            print(cnumbers)
            text = "I will pick all open changes: " + cnumbers
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=text,
                            parse_mode="Markdown")
            global rpick
            cnumbers.replace(" ", "%20")
            cnumbers_url = cnumbers.replace(" ", "%20")
            rpick = cnumbers_url

def choosebuild(bot, update):
    if update.message.from_user.id == int(config['ADMIN']['id']):
        keyboard = [[InlineKeyboardButton("Without Paramaters", callback_data='build')],

                    [InlineKeyboardButton("With Parameters", callback_data='buildWithParameters')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose a build style:', reply_markup=reply_markup)

def sync(bot, update):
    if update.message.from_user.id == int(config['ADMIN']['id']):
        keyboard = [[InlineKeyboardButton("YES", callback_data='syncon')],

                    [InlineKeyboardButton("NO", callback_data='syncoff')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Would you like to sync on a new build?:', reply_markup=reply_markup)

def clean(bot, update):
    if update.message.from_user.id == int(config['ADMIN']['id']):
        keyboard = [[InlineKeyboardButton("YES", callback_data='cleanon')],

                    [InlineKeyboardButton("NO", callback_data='cleanoff')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Would you like to clean on a new build?:', reply_markup=reply_markup)

def buildwithparams(bot, update, query):
    query = update.callback_query
    bot.sendMessage(chat_id=query.message.chat_id,
                    text="You have selected the 'buildWithParameters option, this will include a custom changelog with your build, and will specify whether to sync & clean or not",
                    parse_mode="Markdown")
    user_id = update.callback_query.from_user.id
    try:
        cg
    except NameError:
        bot.sendMessage(chat_id=query.message.chat_id,
                        text="You have selected the 'buildWithParameters option, but the changelog is empty. Please use /changelog + 'text' to provide a changlog for your users.",
                        parse_mode="Markdown")
        return 1
    try:
        syncparam
    except NameError:
        bot.sendMessage(chat_id=query.message.chat_id,
                text="You have selected the 'buildWithParameters option, but have not specified whether you would like to sync before building. Please use /sync to do so.",
                parse_mode="Markdown")
        return 1
    try:
        cleanparam
    except NameError:
        bot.sendMessage(chat_id=query.message.chat_id,
                text="You have selected the 'buildWithParameters option, but have not specified whether you would like to clean before building. Please use /clean to do so.",
                parse_mode="Markdown")
        return 1
    try:
        repopickstatus
    except NameError:
        bot.sendMessage(chat_id=query.message.chat_id,
                        text="You have selected the 'buildWithParameters option, but repopick isn't turned on or off. Turn it on or off with /repopick",
                        parse_mode="Markdown")
        return 1
    if repopickstatus == "true":
        try:
            rpick
        except NameError:
            bot.sendMessage(chat_id=query.message.chat_id,
                            text="You have selected the 'buildWithParameters option, repopick is on, but it's empty. Please use /repopick + 'changes' to pick changes from gerrit, or turn repopick off with /repopick",
                            parse_mode="Markdown")
            return 1
    if cg:
        if syncparam:
            if cleanparam:
                global changelog
                changelog = quote_plus('cg')
                command_string = jenkins + "/job/" + job + "/buildWithParameters?token=" + token + "&changelog=" + cg + "&SYNC=" + syncparam + "&CLEAN=" + cleanparam + "&repopicks=" + rpick
                command = "curl --user " + user + ":" + password + " " + "'" + command_string + "'"
                print (command)
                if user_id == int(config['ADMIN']['id']):
                    bot.sendChatAction(chat_id=query.message.chat_id,
                                       action=ChatAction.TYPING)
                    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    output = output.stdout.read().decode('utf-8')
                    output = '`{0}`'.format(output)

                    bot.sendMessage(chat_id=query.message.chat_id,
                                    text=output,
                                    parse_mode="Markdown")
            else:
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="You have selected the 'buildWithParameters option, but have not specified whether you would like to clean before building. Please use /clean to do so.",
                                parse_mode="Markdown")
        else:
            bot.sendMessage(chat_id=query.message.chat_id,
                            text="You have selected the 'buildWithParameters option, but have not specified whether you would like to sync before building. Please use /sync to do so.",
                            parse_mode="Markdown")
    else:
        bot.sendMessage(chat_id=query.message.chat_id,
                            text="You have selected the 'buildWithParameters option, but the changelog is empty. Please use /changelog + 'text' to provide a changlog for your users.",
                            parse_mode="Markdown")


def buildwithoutparams(bot, update, query):
    user_id = update.callback_query.from_user.id
    command_string = jenkins + "/job/" + job + "/buildWithParameters?token=" + token
    command = "curl --user " + user + ":" + password + " " + "'" + command_string + "'"
    print (command)
    if user_id == int(config['ADMIN']['id']):
        bot.sendChatAction(chat_id=query.message.chat_id,
                           action=ChatAction.TYPING)
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = output.stdout.read().decode('utf-8')
        output = '`{0}`'.format(output)

        bot.sendMessage(chat_id=query.message.chat_id,
                        text=output, parse_mode="Markdown")

def changelog(bot, update, args):
        if update.message.from_user.id == int(config['ADMIN']['id']):
            global cg
            user = update.message.from_user

            str_args = ' '.join(args)
            if str_args != "":
                update.message.reply_text('Changelog updated: ' + "'" + str_args + "'")
                cgs = '%20'.join(args)
                cg = cgs
                print ("Changelog set to " + "'" + cg + "'")
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="You cannot provide an empty changelog.",
                                parse_mode="Markdown")

def repopick(bot, update, args):
        if update.message.from_user.id == int(config['ADMIN']['id']):
            global rpick
            user = update.message.from_user

            str_args = ' '.join(args)
            if str_args != "":
                update.message.reply_text('I will pick changes: ' + "'" + str_args + "'")
                rpicks = '%20'.join(args)
                rpick = rpicks
                print ("Repopick set to" + "'" + rpick + "'")
            else:
                keyboard = [[InlineKeyboardButton("ON", callback_data='repopickon')],

                            [InlineKeyboardButton("OFF", callback_data='repopickoff')]]

                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text('Turn repopick ON or OFF:', reply_markup=reply_markup)

def button(bot, update, direct=True):
        user_id = update.callback_query.from_user.id
        if user_id == int(config['ADMIN']['id']):
            query = update.callback_query

            selected_button = query.data
            global cleanparam
            global syncparam
            global repopickstatus
            if selected_button == 'buildWithParameters':
                bot.editMessageText(text="Selected option: With Paramaters",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                buildwithparams(bot, update, query)
            if selected_button == 'build':
                bot.editMessageText(text="Selected option: Without Paramaters",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                buildwithoutparams(bot, update, query)
            if selected_button == 'syncon':
                bot.editMessageText(text="Selected option: YES",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                syncparam = "true"
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="Sync set to true",
                                parse_mode="Markdown")
            if selected_button == 'syncoff':
                bot.editMessageText(text="Selected option: NO",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                syncparam = "false"
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="Sync set to false",
                                parse_mode="Markdown")
            if selected_button == 'cleanon':
                bot.editMessageText(text="Selected option: YES",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                cleanparam = "true"
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="Clean set to true",
                                parse_mode="Markdown")
            if selected_button == 'cleanoff':
                bot.editMessageText(text="Selected option: NO",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                cleanparam = "false"
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="Clean set to false",
                                parse_mode="Markdown")
            if selected_button == 'repopickon':
                bot.editMessageText(text="Selected option: ON",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                repopickstatus = "true"
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="repopick set to ON",
                                parse_mode="Markdown")
            if selected_button == 'repopickoff':
                bot.editMessageText(text="Selected option: OFF",
                                    chat_id=query.message.chat_id,
                                    message_id=query.message.message_id)
                repopickstatus = "false"
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="repopick set to OFF",
                                parse_mode="Markdown")
        else:
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="You trying to spam me bro?",
                                parse_mode="Markdown")
        return False

def inlinequery(bot, update):
    query = update.inline_query.query
    o = execute(query, update, direct=False)
    results = list()

    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title=query,
                                            description=o,
                                            input_message_content=InputTextMessageContent(
                                            '*{0}*\n\n{1}'.format(query, o),
                                            parse_mode="Markdown")))

    bot.answerInlineQuery(update.inline_query.id, results=results, cache_time=10)

if jenkinsconfig == "yes":
    pickopen_handler = CommandHandler('pickopen', pickopen)
    sync_handler = CommandHandler('sync', sync)
    clean_handler = CommandHandler('clean', clean)
    build_handler = CommandHandler('build', choosebuild)
    repopick_handler = CommandHandler('repopick', repopick, pass_args=True)
    changelog_handler = CommandHandler('changelog', changelog,  pass_args=True)

start_handler = CommandHandler('start', start)
open_handler = CommandHandler('open', openchanges, pass_args=True)
help_handler = CommandHandler('help', help_message, pass_args=True)
link_handler = CommandHandler('link', link, pass_args=True)
note_handler = CommandHandler('note', note, pass_args=True)
time_handler = CommandHandler('time', time_command, pass_args=True)
kick_handler = CommandHandler('kick', kick_user, pass_args=True)

if jenkinsconfig == "yes":
    dispatcher.add_handler(pickopen_handler)
    dispatcher.add_handler(sync_handler)
    dispatcher.add_handler(clean_handler)
    dispatcher.add_handler(build_handler)
    dispatcher.add_handler(repopick_handler)
    dispatcher.add_handler(changelog_handler)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(open_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(link_handler)
dispatcher.add_handler(note_handler)
dispatcher.add_handler(time_handler)
dispatcher.add_handler(kick_handler)
dispatcher.add_handler(MessageHandler([Filters.all], receiveMessage))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(InlineQueryHandler(inlinequery))
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
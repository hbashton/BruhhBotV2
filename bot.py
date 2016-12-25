#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import configparser
import urllib
from urllib.request import urlopen
from urllib.parse import quote_plus
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from uuid import uuid4
import subprocess
import time
import logging
import json
from json import JSONDecoder
from functools import partial

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


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

dispatcher = updater.dispatcher


def start(bot, update):
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
                            text="Sup *not* master. \nHere's a list of commands for you to use:\n/open to see all open changes\n/link `change numbers` to get a link to gerrit changes\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
        else:
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
            time.sleep(1)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup *not* master. \nHere's a list of commands for you to use:\n/open to see all open changes\n/link `change numbers` to get a link to gerrit changes\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
    else:
        if jenkinsconfig == "yes":
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup @hunter_bruhh ! \nHere's a list of commands for you to use:\n/build to start the build process\n/changelog 'text' to set the changelog\n/sync to set sync to on/off\n/clean to set clean to on/off\n/repopick " + "`" + "changes"+ "`" + " to pick from gerrit on build\n/repopick to set repopick on or off\n/open to see all open changes\n/pickopen to pick all open changes on gerrit\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup @hunter_bruhh ! \nHere's a list of commands for you to use:\n/open to see all open changes\n/open `projects` to see open changes for certain projects\n/link `change numbers` to get links to changes on gerrit\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
                           
def help_message(bot, update):
    if update.message.from_user.id != int(config['ADMIN']['id']):
        if jenkinsconfig == "yes":
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
            time.sleep(1)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup *not* master. \nHere's a list of commands for you to use:\n/open to see all open changes\n/open `projects` to see open changes for certain projects\n/link `change numbers` to get a link to gerrit changes\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
        else:
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
            time.sleep(1)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup *not* master. \nHere's a list of commands for you to use:\n/open to see all open changes\n/open `projects` to see open changes for certain projects\n/link `change numbers` to get a link to gerrit changes\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
    else:
        if jenkinsconfig == "yes":
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup @hunter_bruhh ! \nHere's a list of commands for you to use:\n/build to start the build process\n/changelog 'text' to set the changelog\n/sync to set sync to on/off\n/clean to set clean to on/off\n/repopick " + "`" + "changes"+ "`" + " to pick from gerrit on build\n/repopick to set repopick on or off\n/open to see all open changes\n/open `projects` to see open changes for certain projects\n/pickopen to pick all open changes on gerrit\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Sup @hunter_bruhh ! \nHere's a list of commands for you to use:\n/open to see all open changes\n/open `projects` to see open changes for certain projects\n/link `change numbers` to get links to changes on gerrit\n/help to see this message :)")
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)

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
                    openc = openc + "\n" + str(data[i]['_number']) + " - " + str(data[i]['subject'])
                    
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
                openc = openc + "\n" + str(data[i]['_number']) + " - " + str(data[i]['subject'])
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
                            text=openc)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=cnum,
                            parse_mode="Markdown")
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=openc)


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
    start_handler = CommandHandler('start', start)
    sync_handler = CommandHandler('sync', sync)
    clean_handler = CommandHandler('clean', clean)
    build_handler = CommandHandler('build', choosebuild)
    repopick_handler = CommandHandler('repopick', repopick, pass_args=True)
    changelog_handler = CommandHandler('changelog', changelog,  pass_args=True)

open_handler = CommandHandler('open', openchanges, pass_args=True)
help_handler = CommandHandler('help', help_message)
link_handler = CommandHandler('link', link, pass_args=True)

if jenkinsconfig == "yes":
    dispatcher.add_handler(pickopen_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(sync_handler)
    dispatcher.add_handler(clean_handler)
    dispatcher.add_handler(build_handler)
    dispatcher.add_handler(repopick_handler)
    dispatcher.add_handler(changelog_handler)

dispatcher.add_handler(open_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(link_handler)

dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(InlineQueryHandler(inlinequery))
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()

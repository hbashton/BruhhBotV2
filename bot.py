# -*- coding: utf-8 -*-

import configparser
from urllib.parse import quote_plus
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from uuid import uuid4
import subprocess
import time
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


config = configparser.ConfigParser()
config.read('bot.ini')

updater = Updater(token=config['KEYS']['bot_api'])
dispatcher = updater.dispatcher


def start(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id, text="Hi. I'm Hunter's Jenkins Bot! You can use me to start builds, assuming your name is @hunter_bruhh! If not, then I'm not much use to you right now! Maybe he'll implement some cool stuff later!")
    if update.message.from_user.id != int(config['ADMIN']['id']):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        time.sleep(1)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="It seems like you aren't allowed to use me. :(")
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
    else:
        keyboard = [[InlineKeyboardButton("build", callback_data='build')],

                    [InlineKeyboardButton("buildWithParameters", callback_data='buildWithParameters')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose a build style:', reply_markup=reply_markup)


#def execute(bot, update, direct=True):
#
#    try:
#        user_id = update.message.from_user.id
#        command = update.message.text
#        inline = False
#    except AttributeError:
#        # Using inline
#        user_id = update.inline_query.from_user.id
#        command = update.inline_query.query
#        inline = True
#
#    if user_id == int(config['ADMIN']['id']):
#        if not inline:
#            bot.sendChatAction(chat_id=update.message.chat_id,
#                               action=ChatAction.TYPING)
#        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#        output = output.stdout.read().decode('utf-8')
#        output = '`{0}`'.format(output)
#
#        if not inline:
#            bot.sendMessage(chat_id=update.message.chat_id,
#                        text=output, parse_mode="Markdown")
#            return False
#
#        if inline:
#            return output

def changelog(bot, update, args):
    if update.message.from_user.id == int(config['ADMIN']['id']):
        global cg
        user = update.message.from_user
        update.message.reply_text('Changelog updated')
        cgs = '%20'.join(args)
        cg = cgs
        print (cg)
    return cg

def build(bot, update, direct=True):
        user_id = update.callback_query.from_user.id
        if user_id == int(config['ADMIN']['id']):
            query = update.callback_query

            bot.editMessageText(text="Selected option: %s" % query.data,
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id)
            selected_button = query.data
            changelog = quote_plus('cg')
            if selected_button == 'buildWithParameters':
                bot.sendMessage(chat_id=query.message.chat_id,
                                text="You have selected the 'buildWithParameters option, this will include a custom changelog with your build. You must provide the changelog with /changelog [text], or this build will fail", parse_mode="Markdown")
                user_id = update.callback_query.from_user.id
                command_string = "https://jenkins.hunterbruhh.me/job/halogenOS/buildWithParameters?token=MYTOKENGOESHERE&changelog=" + cg
                command = "curl --user user:pass " + "'" + command_string + "'"
                print (command)
                if user_id == int(config['ADMIN']['id']):
                     bot.sendChatAction(chat_id=query.message.chat_id,
                                        action=ChatAction.TYPING)
                output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = output.stdout.read().decode('utf-8')
                output = '`{0}`'.format(output)
    
                bot.sendMessage(chat_id=query.message.chat_id,
                                text=output, parse_mode="Markdown")
            if selected_button == 'build':
                user_id = update.callback_query.from_user.id
                command_string = "https://jenkins.hunterbruhh.me/job/halogenOS/buildWithParameters?token=MYTOKENGOESHERE"
                command = "curl --user user:pass " + "'" + command_string + "'"
                print (command)
                if user_id == int(config['ADMIN']['id']):
                     bot.sendChatAction(chat_id=query.message.chat_id,
                                        action=ChatAction.TYPING)
                output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = output.stdout.read().decode('utf-8')
                output = '`{0}`'.format(output)
    
                bot.sendMessage(chat_id=query.message.chat_id,
                                text=output, parse_mode="Markdown")
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


start_handler = CommandHandler('start', start)
build_handler = CommandHandler('build', build)
changelog_handler = CommandHandler('changelog', changelog,  pass_args=True)

dispatcher.add_handler(changelog_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(CallbackQueryHandler(build))
dispatcher.add_handler(InlineQueryHandler(inlinequery))
dispatcher.add_handler(changelog_handler)

dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()

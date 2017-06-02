# -*- coding: utf-8 -*-
# Alert/Info Bot v0.0
# Probably better to implement using a class
# John Song
# May 31 2017

from slackclient import SlackClient
import sys
import info
import datetime
from time import sleep

# Slack Token for app
token = 'xoxp-2154625182-190672578374-190017115328-a2b63e101c1f938da030c6c86ba45def'
sc = SlackClient(token)

# Slack Token for bot
bot_token = 'xoxb-191262507666-b60ESfb7karu3hSGrEGHKM13'
sc_bot = SlackClient(bot_token)

# Connect to RTM
rtm = sc_bot.rtm_connect()

msg_interval = 15 # Seconds

# Function for sendng message/attachments
def send_msg(message, attachment, chan, now, last_sent):
	time_last_msg = (now - last_sent).seconds
	neg_time_last_msg = (last_sent - now).seconds

	# Wait until message interval passes (prevent spam)
	if neg_time_last_msg < 60: # Deal with negative time_last_msg
		print('Waiting for ' + str(60 - neg_time_last_msg) + ' seconds until sending next message.')
		sleep(60 - neg_time_last_msg)
		print('Sending message...')

	elif time_last_msg < msg_interval:
		print('Waiting for ' + str(msg_interval - time_last_msg) + ' seconds until sending next message.')
		sleep(msg_interval - time_last_msg)
		print('Sending message...')

	# Send message to Slack
	if not isinstance(message,str):
		message = 'Error: Message not a string'
	if not attachment:
		sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message)
	else:
		sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message, attachments=attachment)

	# Record the time that the message was sent
	send_time = datetime.datetime.now()
	send_time = send_time - datetime.timedelta(microseconds=now.microsecond)
	return send_time

# Some initializers
event_list = []
last_sent = datetime.datetime.strptime('Jan', '%b')

while True:
	# Current time (MM/DD/YYYY HH:mm)
	now = datetime.datetime.now()
	now = now - datetime.timedelta(seconds=now.second,
		microseconds=now.microsecond)

	# Event alerts
	if event_list:
		alert_list, event_list = info.event_alerts(event_list, now)
		if alert_list:
			print('Alert List')
			msg, att, chan = info.compose_message(alert_list, now)
			last_sent = send_msg(msg, att, chan, now, last_sent)

	# Parse channel messages
	rcvd_call = ['-1']
	red = sc_bot.rtm_read()
	for call in red:
		if call['type'] == 'message':
			rcvd_call = call['text'].split()
			command = rcvd_call[0]
			command_tags = rcvd_call[1:]

			# List of commands
			if command == '!parse':
				event_list = info.event_parse(command_tags, now)
			elif command == '!events':
				msg, att, chan = info.compose_message(event_list, now)
				print(now)
				print(last_sent)
				last_sent = send_msg(msg, att, chan, now, last_sent)
			elif command == '!alert':
				last_sent = send_msg(alert.message, alert.attachment, alert.chan, now)

	# Kill command
	if rcvd_call == 'Kill Alert Bot!':
		print('Killed')
		break
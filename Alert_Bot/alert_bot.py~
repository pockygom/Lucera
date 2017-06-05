# -*- coding: utf-8 -*-
# Alert/Info Bot v0.0
# Probably better to implement using a class
# John Song
# May 31 2017

from slackclient import SlackClient
import sys
import os
import info
from datetime import datetime, timedelta
from time import sleep

# Slack Token for app
token = os.environ.get('SLACK_TOKEN')
sc = SlackClient(token)

# Slack Token for bot
bot_token = os.environ.get('SLACK_BOT_TOKEN')
sc_bot = SlackClient(bot_token)

# Connect to RTM
rtm = sc_bot.rtm_connect()

msg_interval = 60 # Seconds

# Function for sendng message/attachments
def send_msg(message, attachment, chan, now):
	# Send message to Slack
	if not isinstance(message,str):
		message = 'Error: Message not a string'
	if not attachment:
		sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message)
	else:
		sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message, attachments=attachment)

	# Record the time that the message was sent
	send_time = datetime.now()
	send_time = send_time - timedelta(microseconds=now.microsecond)

	# Wait until message interval passes (prevent spam)
	time_into_minute = (send_time - now).seconds
	if time_into_minute < 60: # Wait until next second
		print('Waiting for ' + str(60 - time_into_minute) + ' seconds until next command.')
		sleep(60 - time_into_minute)
		print('Sending message...')
	return(send_time)

# Some initializers
event_list = []
last_sent = datetime.strptime('Jan', '%b')

while True:
	# Current time (MM/DD/YYYY HH:mm)
	now = datetime.now()
	now = now - timedelta(seconds=now.second,
		microseconds=now.microsecond)

	# Event alerts
	if event_list:
		alert_list, event_list = info.event_alerts(event_list, now)
		if alert_list:
			msg, att = info.compose_event_message(alert_list, now)
			send_msg(msg, att, info.chan, now)
			print('Alert sent at %s' % str(send_time))

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
				print('Parsing list of upcoming events with the following tags: %s.' % command_tags)
				event_list = info.event_parse(command_tags, now)
				parse_msg = 'Parsing complete. Includes events with the following tags: %s.' % command_tags
				send_msg(parse_msg, [], info.chan, now)
			elif command == '!events':
				print('Sending upcoming event list.')
				msg, att = info.compose_event_message(event_list, now)
				send_msg(msg, att, info.chan, now)
			elif command == '!alert':
				print('Sending log of recent latency alerts.')
				send_msg(msg, att, alert.chan, now)

	# Kill command
	if rcvd_call == 'Kill Alert Bot!':
		print('Killed')
		break

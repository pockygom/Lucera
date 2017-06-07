# -*- coding: utf-8 -*-
# Alert/Info Bot v0.0
# Probably better to implement using a class
# John Song
# May 31 2017

# Modules
from slackclient import SlackClient
from time import sleep
from datetime import datetime, timedelta
import pytz
import sys
import os

# Functionality files
import info
import latency_alert as lat_alert

# Slack Token for app
token = os.environ.get('SLACK_TOKEN')
sc = SlackClient(token)

# Slack Token for bot
bot_token = os.environ.get('SLACK_BOT_TOKEN')
sc_bot = SlackClient(bot_token)

# Connect to RTM
while True:
	print('Connecting...')
	if sc_bot.rtm_connect():
		print('Connected!')
		break

# Messaging interval to prevent spamming
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
	print('Sending message...')

	# Record the time that the message was sent
	send_time = info.eastern.localize(datetime.now())
	send_time = send_time - timedelta(microseconds=now.microsecond)

	# Wait until message interval passes (prevent spam)
	time_into_minute = (send_time - now).seconds
	if time_into_minute < msg_interval: # Wait until next second
		wait_time = msg_interval - time_into_minute
		print('Waiting for ' + str(wait_time) + ' seconds until next command.')
		sleep(wait_time)
	return(send_time)

# Some initializers
event_list = []
kill_switch = False

while True:
	# Current time (MM/DD/YYYY HH:mm)
	now = info.eastern.localize(datetime.now())
	now = now - timedelta(seconds=now.second,
		microseconds=now.microsecond)

	# Event alerts
	if event_list:
		alert_list, event_list = info.event_alerts(event_list, now)
		if alert_list:
			msg, att = info.compose_event_message(alert_list, now)
			send_time = send_msg(msg, att, info.chan, now)
			print('%s: Alerts sent!' % str(send_time))

	# Parse channel messages
	rcvd_call = ['-1']
	rcvd = sc_bot.rtm_read()
	for call in rcvd:
		if call['type'] == 'message':
			print(call)
			rcvd_call = call['text'].split()
			command = rcvd_call[0]
			command_tags = rcvd_call[1:]

			# Check the channel the message is from and use corresponding commands
			#if call['channel'] == info.chan_enc:
			if command == '!parse':
				print('%s: Parsing list of upcoming events with the following tags: %s.' % (str(now), command_tags))
				event_calender, event_list = info.event_parse(command_tags, now)
				if not command_tags:
					parse_msg = 'Parsing complete. Includes all events.' 
				else:
					parse_msg = 'Parsing complete. Includes events with the following tags: %s.' % command_tags
				_, att = info.compose_event_message(event_list, now)
				_ = send_msg(parse_msg, att, info.chan, now)
				event_calender, event_list = info.update_event_list(command_tags, now)

			elif command == '!events':
				print('%s: Sending list of upcoming events.' % str(now))
				msg, att = info.compose_event_message(event_list, now)
				_ = send_msg(msg, att, info.chan, now)

			#elif call['channel'] == lat_alert.chan_enc:
			if command == '!alert':
				print('%s: Sending log of recent latency alerts.' % str(now))

			# Kill command
			if call['text'] == 'Kill Alert Bot!':
				print('%s: Killed' % str(now))
				kill_switch = True
				break

	sys.stdout.flush()

	if kill_switch:
		sys.stdout.flush()
		break
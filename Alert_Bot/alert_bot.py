# -*- coding: utf-8 -*-
# Alert/Info Bot v0.0
# Probably better to implement using a class
# John Song
# May 31 2017

# Modules
from slackclient import SlackClient
from threading import Timer
from time import sleep
from datetime import datetime, timedelta
import pytz
import sys
import os

# Functionality files
import event
import latency_alert as alert

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

# Function for sendng message/attachments
def send_msg(message, attachment, chan, now, last_sent, user=None):
	# Wait until message interval passes (prevent spam)
	if now == last_sent: # Wait until next minute
		if user:
			message = 'Requesting for messages too quickly. Wait for the next minute.'
			sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message)
		return(last_sent)

	# Send message to Slack
	if not isinstance(message,str):
		message = 'Error: Message not a string'
	if not attachment:
		sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message)
	else:
		sc.api_call('chat.postMessage', asuser=True, channel=chan, text=message, attachments=attachment)
	print('%s: Sending message...' % str(datetime.now()))

	# Record the time that the message was sent
	send_time = event.eastern.localize(datetime.now())
	send_time = send_time - timedelta(seconds=send_time.second, microseconds=send_time.microsecond)
	return(send_time)

# Some initializers
event_list = []
send_time = event.eastern.localize(datetime(1990,1,1,0,0))
send_time = send_time - timedelta(seconds=send_time.second, microseconds=send_time.microsecond)
event_send_time = send_time
event_thread = []
event_timers
alert_thread = []
alert_msg = []
kill_switch = False

while True:
	# Current time (MM/DD/YYYY HH:mm)
	now = event.eastern.localize(datetime.now())
	now = now - timedelta(seconds=now.second, microseconds=now.microsecond)

	# Event alerts
	if event_send_time != now:
		if event_list:
			event_alert_list, event_list = event.event_alerts(event_list, now)
			if event_alert_list:
				event_msg, event_att = event.compose_event_message(event_alert_list, now)
				event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time)
				print('%s: Event alerts sent for %s!' % (str(datetime.now()), str(event_send_time)))

	if alert_msg:
		alert_send_time = send_msg(alert_msg, alert_att, alert.chan, now, alert_send_time)
		print('%s: Latency alerts sent for %s!' % (str(datetime.now()), str(event_send_time)))
		alert_msg = []

	# Parse channel messages
	rcvd_call = ['-1']
	rcvd = sc_bot.rtm_read()
	for call in rcvd:
		if call['type'] == 'message':
			print('%s: Received message: %s' % (str(datetime.now()), call['text']))
			sys.stdout.flush()
			rcvd_call = call['text'].split()
			command = rcvd_call[0].lower()
			command_tags = [command_tag.lower() for command_tag in rcvd_call[1:]]

			# Check the channel the message is from and use corresponding commands
			if call['channel'] == event.chan_enc:
				if command == '!parse':
					if event_thread:
						event_thread.cancel()
					print('%s: Parsing list of upcoming events with the following tags: %s.' % (str(datetime.now()), command_tags))
					event_calender, event_list, output_tags, event_thread = event.update_event_list(command_tags, now)
					if not output_tags:
						parse_msg = 'Parsing complete. Includes all events.' 
					else:
						parse_msg = 'Parsing complete. Includes events with the following tags: %s.' % output_tags
					_, event_att = event.compose_event_message(event_list, now)
					event_send_time = send_msg(parse_msg, event_att, event.chan, now, event_send_time, user=True)

				elif command == '!events':
					print('%s: Sending list of upcoming events.' % str(datetime.now()))
					event_msg, event_att = event.compose_event_message(event_list, now)
					event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time, user=True)
				
				elif command == '!timers':
					print('%s: Adding timers to the list of timers: %s' % (str(datetime.now()), command_tags))
					for tag in command_tags:
						if isinstance(tag, int):
							if tag not in event_timer:
								event_timer.append(tags)
					event_msg = 'The current timer list includes: %s (in minutes)' % event_timer
					event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time, user=True)

				elif command == '!help':
					print('%s: Printing list of commands for event alerts.' % str(datetime.now()))
					event_msg, event_att = event.command_list()
					event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time, user=True)

			elif call['channel'] == alert.chan_enc:
				if command == '!startalert':
					if alert_timer:
						alert_timer.cancel()
					print('%s: Initiating log of latency alerts.' % str(datetime.now()))
					alert_msg, alert_att = alert.update_list(command_tags)
				
				elif command == '!help':
					print('%s: Printing list of commands for latency alerts.' % str(datetime.now()))
					alert_msg, alert_att = alert.command_list()
					alert_send_time = send_msg(alert_msg, alert_att, alert.chan, now, alert_send_time, user=True)

			# Kill command
			elif call['channel'] == 'D5M9ATXSQ': # Only pockygom can kill
				if call['text'] == 'Kill Alert Bot!':
					print('%s: Killed' % str(datetime.now()))
					kill_switch = True
					break

	# Print outputs to file
		sys.stdout.flush()
	sys.stdout.flush()

	if kill_switch:
		break

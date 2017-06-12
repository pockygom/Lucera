# -*- coding: utf-8 -*-
# Alert/Info Bot v0.2
# Probably better to implement using a class
# John Song
# May 31 2017

# Modules
from slackclient import SlackClient
from datetime import datetime, timedelta
import sys
import os

# Functionality files
import info as event
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
alert_send_time = send_time
event_timers = [0]
event_tags = []
alert_thresh = alert.def_thresh
alert_delta_list = []
alert_msg = []
kill_switch = False

while True:
	# Current time (MM/DD/YYYY HH:mm)
	now = event.eastern.localize(datetime.now())
	now = now - timedelta(seconds=now.second, microseconds=now.microsecond)

	# Event updater
	if event_send_time != now:
		if event_list:
			event_alert_list, event_list = event.event_alerts(event_list, event_timers, now)
			if event_alert_list:
				print('%s: Sending event alerts!' % str(datetime.now()))
				event_msg, event_att = event.compose_message(event_alert_list, now)
				event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time)
		else:
			print('%s: Autoupdating event list!' % str(datetime.now()))
			event_calender, event_list, event_tags = event.update_event_list(event_tags, now)

	# Alert updater
	if alert_send_time != now:
		if alert_thresh:
			alert_msg, alert_att, alert_delta_list, alert_dbs_keys, alert_thresh = alert.update_list(alert_thresh, alert_delta_list)
			if alert_msg:
				print('Sending latency alerts!')
				alert_send_time = send_msg(alert_msg, alert_att, alert.chan, now, send_time)
				alert_msg = []
			else:
				print('No latency alerts found!')
				alert_send_time = now

	# Parse channel messages
	rcvd_call = ['-1']
	rcvd = sc_bot.rtm_read()
	for call in rcvd:
		if call['type'] == 'message':
			print('%s: Received message: %s' % (str(datetime.now()), call['text']))
			rcvd_call = call['text'].split()
			command = rcvd_call[0].lower()
			command_tags = [command_tag.lower() for command_tag in rcvd_call[1:]]

			# Check the channel the message is from and use corresponding commands
			if call['channel'] == event.chan_enc:
				if command == '!parse':
					print('%s: Parsing list of upcoming events with the following tags: %s.' % (str(datetime.now()), command_tags))
					event_calender, event_list, event_tags = event.update_event_list(command_tags, now)
					if not event_tags:
						parse_msg = 'Parsing complete. Includes all events.' 
					else:
						parse_msg = 'Parsing complete. Includes events with the following tags: %s.' % event_tags
					_, event_att = event.compose_message(event_list, now)
					event_send_time = send_msg(parse_msg, event_att, event.chan, now, event_send_time, user=True)

				elif command == '!events':
					print('%s: Sending list of upcoming events.' % str(datetime.now()))
					event_msg, event_att = event.compose_message(event_list, now)
					event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time, user=True)
				
				elif command == '!timers':
					for tag in command_tags:
						try:
							int(tag)
							is_int = True
						except ValueError:
							is_int = False
						if is_int:
							new_timer = int(tag)
							if new_timer > 0:
								if new_timer not in event_timers:
									event_timers.append(new_timer)
					event_msg = 'The current timer list includes: %s (in minutes)' % event_timers
					print('%s: The current list of timers: %s' % (str(datetime.now()), str(event_timers)))
					event_att = []
					event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time, user=True)

				elif command == '!help':
					print('%s: Printing list of commands for event alerts.' % str(datetime.now()))
					event_msg, event_att = event.command_list()
					event_send_time = send_msg(event_msg, event_att, event.chan, now, event_send_time, user=True)

			elif call['channel'] == alert.chan_enc:
				if command == '!startalert':
					if alert_thread:
						alert_thread.cancel()
					if command_tags:
						command_tag = command_tags[0]
					else:
						command_tag = []
					print('%s: Initiating log of latency alerts.' % str(datetime.now()))
					alert_msg, alert_att, alert_delta_list, alert_dbs_keys, alert_thresh = alert.update_list(command_tag)

				elif command == '!alertlist':
					if alert_delta_list:
						print('%s: Sending list of market data awaiting updates.' % str(datetime.now()))
						alert_msg, alert_att = alert.compose_message([], [], alert_dbs_keys, alert_delta_list, user=True)
						alert_send_time = send_msg(alert_msg, alert_att, alert.chan, now, alert_send_time-timedelta(seconds=30), user=True)
						alert_send_time += timedelta(seconds=30)
						alert_msg = []

				elif command == '!help':
					print('%s: Printing list of commands for latency alerts.' % str(datetime.now()))
					alert_msg, alert_att = alert.command_list()
					alert_send_time = send_msg(alert_msg, alert_att, alert.chan, now, send_time, user=True)

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

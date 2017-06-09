# -*- coding: utf-8 -*-
# Event tracker
# John Song
# May 31 2017

# Creating a class is probably better...
# Creating a list for event times is probably better too...

import csv
import requests
from threading import Timer
from datetime import datetime, timedelta, date
import pytz

# Slack channel
chan = 'lumefx-data-info'
chan_enc = 'C5LJANRSQ'

# Calender update interval in seconds
calender_update_timer = 1800 # Half hour

# Current year
current_year = [str(datetime.now().year)]

# Time zones
eastern = pytz.timezone('US/Eastern')
utc = pytz.utc

# Time format
time_fmt = '%b %d %H:%M %Z %Y'

# Importance tag
imp_ids = ['high', 'medium', 'low']
imp_ind = 5
imp_colors = {'High': 'danger', 'Medium': 'warning', 'Low': '#FFDB99'}

# Event CSV getter
def get_cal():
	# Initialize
	event_calender = []

	# Get url for the csv
	now = date.today()
	prev_sunday = now - timedelta(days=now.weekday() + 1 % 7)
	csv_url = 'https://www.dailyfx.com/files/Calendar-' + prev_sunday.strftime('%m-%d-%Y') + '.csv'
	print('Downloading calendar from %s.' % csv_url)

	# Formatting
	r = requests.get(csv_url)
	cal_csv = r.text.split('\n')
	del(cal_csv[0]) # Remove header
	for row in cal_csv:
		event_calender.append(row.split(','))
	return(event_calender)

# Event CSV Updater
def update_event_list(command_tags, curr_time):
	# Generate calender, list and output_tags
	event_calender, event_list, output_tags = event_parse(command_tags, curr_time)
	print('%s: Event list refreshed.' % str(datetime.now()))

	# Start new timer to repeat
	cal_timer = Timer(calender_update_timer, update_event_list, [command_tags, curr_time])
	cal_timer.start()
	return(event_calender, event_list, output_tags, cal_timer)

# Parse through the events CSV file
def event_parse(command_tags, curr_time):
	# Initialize
	event_list = []
	event_calender = get_cal()

	# Check for tags
	imp_tags = set(imp_ids).intersection(command_tags)
	output_tags = list(imp_tags)

	# No tags = include all tags
	if not imp_tags:
		imp_tags = imp_ids

	# Parsing event list
	for row in event_calender:
		next_row = False
		if row[0]:
			event_time = conv_time(row)
			if curr_time < event_time: # Search for events that haven't passed.
				for imp_tag in imp_tags:
					if (row[imp_ind].lower() == imp_tag):
						event_list.append(row) # Might change to unique append
						next_row = True
						break

	return(event_calender, event_list, output_tags)

# Compose JSON to send to Slack
def compose_event_message(event_list, curr_time):
	att = []
	if not event_list:
		msg = 'No events available.'
	else:
		msg = 'Upcoming Events!'
		for row in event_list:
			time_until = conv_time(row) - curr_time
			if (time_until.days == 0) & (time_until.seconds == 0):
				value_str = 'Event is happening now!'
			else:
				value_str = 'Time until event: ' + str(time_until)

			# Attachment template for upcoming events
			att_temp = {
					'color': imp_colors[row[imp_ind]],
					'author_name': ' '.join(row[0:3]),
					'title': row[4],
					'fields': [
					{
						'value': value_str 
					}
				]
			}
			att.append(att_temp)
	return(msg, att)

# Determine events to alert based off of timers
def event_alerts(event_list, event_timers, curr_time):
	# Initialize
	event_alert_list = []
	event_del_queue = 0
	
	# Check timers to see if any have been triggered
	for row in event_list:
		time_until = conv_time(row) - curr_time
		for timers in event_timers:
			if (time_until.days == 0) & (time_until.seconds/60 == timers):
				event_alert_list.append(row)
				if timers == event_timers[0]:
					event_del_queue += 1
				break

	# Remove any events that have occurred (Timer = 0 triggered)
	for _ in range(event_del_queue):
		del(event_list[0])
	return(event_alert_list, event_list)

# Convert event times to datetime object
def conv_time(row):
	# Format event time
	event_time_string = ' '.join(row[0:3]).split()[1:5]
	if not row[1]: # When hours and minutes are missing
		event_time_string += ['00:00']
		event_time_string += ['UTC']
	event_time_string += current_year

	# Convert to datetime object
	event_time = datetime.strptime(' '.join(event_time_string), time_fmt)
	event_time = utc.localize(event_time)
	return(event_time.astimezone(eastern))

# Send message consisting of a list of valid commands
def command_list():
	att = []
	msg = 'Valid commands for event alerts include:\n!parse <importance tags>:\n	Importance tags include High, Medium, and Low. Case insensitive.\n	Parses the event list containing the included importance tag.\n	If no tag is given, all events are included.\n!events:\n	Send a message consisting of the entire event list.\n!timers <time in minutes>:\n	Adds a timer to the timer list and prints the timer list.\n	Once the time until an event coincides with a timer in this list, Alert Bot wil send an alert.'
	return(msg, att)


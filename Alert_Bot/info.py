# -*- coding: utf-8 -*-
# Event tracker
# John Song
# May 31 2017

import csv
import requests
from threading import Timer
from datetime import datetime, timedelta, date

# Calender update interval in seconds
calender_update_timer = 30

# Current year
current_year = [str(datetime.now().year)]

# Slack channel
chan = 'lumefx-data-alerts'

# Importance tag
imp_ids = ['High', 'Medium', 'Low']
imp_ind = 5
imp_colors = {'High': 'danger', 'Medium': 'warning', 'Low': '#FFDB99'}

# Currency tag
cur_ids = ['USD', 'EUR', 'JPY']
cur_ind = 3

# Time tag could be useful too. Especially with time zones.

# Set of timers in minutes
event_timers = [0, 5, 15, 30, 60, 120, 360, 720]

# Event CSV url formatter
def get_csv_url(date):
	prev_sunday = date - timedelta(days=date.weekday() + 1 % 7)
	return('https://www.dailyfx.com/files/Calendar-'
		+ prev_sunday.strftime('%m-%d-%Y')
		+ '.csv')

# Event CSV getter
def get_cal():
	event_calender = []
	now = date.today()
	csv_url = get_csv_url(now)
	print('Downloading calendar from {}'.format(csv_url))
	r = requests.get(csv_url)
	cal_csv = r.text.split('\n')
	del(cal_csv[0])
	for row in cal_csv:
		event_calender.append(row.split(','))
	return(event_calender)

# Event CSV Updater
def update_event_list(command_tags, curr_time):
	th = Timer(calender_update_timer, update_event_list, [command_tags, curr_time])
	th.start()
	print('Event list refreshed')
	event_calender, event_list = event_parse(command_tags, curr_time)
	return(event_calender, event_list)

# Parse through the events CSV file
def event_parse(command_tags, curr_time):
	# Initialize
	event_list = []
	event_calender = get_cal()

	# Check for tags
	imp_tags = set(imp_ids).intersection(command_tags)
	cur_tags = set(cur_ids).intersection(command_tags)

	# No tags = include all tags
	if not imp_tags:
		imp_tags = imp_ids
	if not cur_tags:
		cur_tags = cur_ids

	# Parsing event list
	for row in event_calender:
		next_row = False
		if row[0]:
			event_time = conv_time(row)
			if curr_time < event_time: # Search for events that haven't passed.
				for imp_tag in imp_tags:
					for cur_tag in cur_tags:
						if (row[imp_ind] == imp_tag) & (row[cur_ind] == cur_tag):
							event_list.append(row) # Might change to unique append
							next_row = True
							break
					if next_row == True:
						break

	return(event_calender, event_list)

# Compose JSON to send to Slack
def compose_event_message(event_list, curr_time):
	att = []
	if not event_list:
		msg = 'No events available.'
	else:
		msg = 'Upcoming Events'
		for row in event_list:
			time_until = str(conv_time(row) - curr_time)

			# Attachment template for upcoming events
			att_temp = {
					"color": imp_colors[row[imp_ind]],
					"author_name": ' '.join(row[0:3]),
					"title": row[4],
					"fields": [
					{
						"value": "Time until event: " + str(time_until)
					}
				]
			}
			att.append(att_temp)
	return(msg, att)

# Determine events to alert based off of timers
def event_alerts(event_list, curr_time):
	alert_list = []
	event_del_queue = 0
	for row in event_list:
		time_until = conv_time(row) - curr_time
		for timers in event_timers:
			if time_until.seconds/60 == timers:
				alert_list.append(row)
				if timers == event_timers[0]:
					event_del_queue += 1
				break
	for _ in range(event_del_queue):
		del(event_list[0])
	return(alert_list, event_list)

# Convert event times to datetime object
def conv_time(row):
	event_time_format = ' '.join(row[0:3]).split()[1:4]
	if not row[1]:
		event_time_format += ['00:00']
	event_time_format += current_year
	event_time = datetime.strptime(' '.join(event_time_format), '%b %d %H:%M %Y')
	return(event_time)
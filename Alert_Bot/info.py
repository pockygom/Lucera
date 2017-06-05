# -*- coding: utf-8 -*-
# Event tracker
# John Song
# May 31 2017

import csv
from datetime import datetime

# Current year
current_year = [str(datetime.now().year)]

# Event CSV file
path = './Calendar-05-28-2017.csv'

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
event_timers = [-5, 0, 5, 15, 30, 60, 120, 360, 720]

# Parse through the events CSV file
def event_parse(msg_tags, datetime):
	# Initialize
	event_list = []
	with open(path, 'r') as csvfile:
		event_reader = csv.reader(csvfile)
		next(event_reader, None)

		# Check for tags
		imp_tags = set(imp_ids).intersection(msg_tags)
		cur_tags = set(cur_ids).intersection(msg_tags)

		# No tags = include all tags
		if not imp_tags:
			imp_tags = imp_ids
		if not cur_tags:
			cur_tags = cur_ids

		# Parsing event list
		for row in event_reader:
			next_row = False
			event_time = conv_time(row)
			if datetime < event_time: # Search for events that haven't passed.
				for imp_tag in imp_tags:
					for cur_tag in cur_tags:
						if (row[imp_ind] == imp_tag) & (row[cur_ind] == cur_tag):
							event_list.append(row) # Might change to unique append
							next_row = True
							break
					if next_row == True:
						break
		return(event_list)

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
	event_time = ' '.join(row[0:3]).split()[1:4]
	event_time += current_year
	event_time = datetime.strptime(' '.join(event_time), '%b %d %H:%M %Y')
	return(event_time)
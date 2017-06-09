# -*- coding: utf-8 -*-
# Latency Alerts v0.0
# John Song
# May 31 2017

import urllib2 as urllibs
import ast
from threading import Timer
from datetime import datetime, timedelta

# Slack Channel
chan = 'lumefx-data-alerts'
chan_enc = 'C5LEPDXUK'

# API URL
url = 'http://10.1.23.19:8085/summary'
url_req = urllibs.Request(url)

# Data update interval in seconds
data_update_timer = 34

# Relevant data keys ('ref', 'partition', 'ts', 'delta')
delta_key = 'delta'
label_keys = ['partition', 'ts']
ref_key = 'ref'

# Message colors
colors = {'#FFDB99', 'warning', 'danger'}

# Receive and convert data
def get_data():
	# Open url
	data_obj = urllibs.urlopen(url_req)

	# Format data
	data = []
	for line in data_obj:
		new_line = line.decode('utf-8')
		new_line = new_line.replace('null', '[]')
		new_line = new_line.replace('\n', '')
		data.append(new_line)
		if new_line == '  } ]': # Last line of the url
			del(data_obj)
			break

	# Convert string into dictionary
	if data:
		data = ' '.join(data)
		data = ' '.join(data.split()) + ' }'
		data = ast.literal_eval(data)
	return(data)

# Update data and format into a list
def update_data(last_ref, delta_thresh):
	# Initialize
	database_keys = []
	delta_list = []
	dbs_list = []

	# Obtain data dictionary
	data = get_data()
	
	# Obtain keys for existing databases
	for key in data:
		database_keys.append(key)

	# Determine the update time for the market data
	ref_time = data[database_keys[0]][0][ref_key]
	
	# Check if updatse are new and extract relevant information
	if last_ref != ref_time:
		print('%s: Market data refreshed for %s.' % (str(datetime.now()), ref_time)
		for database_key in database_keys:
			for update in data[database_key]:
				if update[delta_key]:
					delta_string = update[delta_key]
					delta_time = conv_delta_time(delta_string)

					# Check if delta is above the threshold and record the update
					if (delta_time.seconds > delta_thresh) & (delta_time.days == 0):
						delta_data_string = ''
						delta_data_string += database_key
						for key in label_keys:
							delta_data_string += ' '
							delta_data_string += update[key]
						delta_list.append(delta_data_string)
	return(delta_list, ref_time)

def update_list(delta_thresh, delta_list=[], last_ref='-1'):
	# Initialize
	delta_dbs_list = []

	# Update list
	delta_list, ref_time = update_data(last_ref, delta_thresh)

	# Chcek if updates are new
	if ref_time == last_ref:
		delta_list = past_delta_list
		delta_list_additions = []
	else: # If they are new determine additions and subtractions from the lists
		delta_list_additions = set(delta_list).difference(past_delta_list)
		delta_list_subtractions = set(past_delta_list).difference(delta_list)
		for addition in delta_list_additions:
			if addition.split()[0] not in delta_dbs_list:
				delta_dbs_list.append(addition.split()[0])

	# Start new timer to repeat list updating
	dat_timer = Timer(data_update_timer, update_list, [delta_list, delta_thresh, ref_time])
	dat_timer.start()

	# Create a message if there are new additions
	if delta_list_additions & delta_list_subtractions:
		msg, att = compose_message(delta_list_additions, delta_list_subtractions, delta_dbs_list)
	return(msg, att)

def conv_delta_time(delta_string):
	# Check if string is valid then convert the delta time into a timedelta object
	if delta_string:
		delta_string = delta_string.split()
		if len(delta_string) == 1: # Check if the delta is greater than or equal to a day
			delta_string.insert(0, '0')
		else:
			del(delta_string[1])
		delta_array = list(map(int, ' '.join(' '.join(delta_string).split(':')).split()))
		delta_time = timedelta(days = delta_array[0], hours = delta_array[1], minutes = delta_array[2], seconds = delta_array[3])
	else:
		delta_time = []
	return(delta_time)

def compose_message(delta_list_additions, delta_list_subtractions delta_dbs_list):
	# Initialize
	att = []
	msg = 'Latency Alerts!'

	# Create an attachment for each database consisting of the additions and subtractions to the list
	for dbs in delta_dbs_list:
		add_str = ''
		sub_str = ''

		# Construct field string for list additions
		i = 0
		for delta in delta_list_additions:
			if delta.split()[0] == dbs:
				add_str += ' '.join(delta.split()[1:]) + '\n'
				i += 1
		
		# Color code for how many additions were detected for a given database
		if i < 5:
			color_code = colors[0]
		elif i < 10:
			color_code = colors[1]
		else:
			color_code = colors[2]

		# Construct field string for list subtractions
		for delta in delta_list_subtractions:
			if delta.split()[0] == dbs:
				sub_str += ' '.join(delta.split()[1:]) + '\n'

		# Attachment template for latency alerts for each database
		att_temp = {
				'color': color_code,
				'author_name': dbs,
				'fields': [
				{
					'title': 'Additions'
					'value': add_str
				}
				{
					'title': 'Subtractions'
					'value': sub_str
				}
			]
		}
		att.append(att_temp)
	return(msg, att)

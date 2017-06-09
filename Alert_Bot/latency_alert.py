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

# Receive and parse data
def get_data():
	# Open url
	data_obj = urllibs.urlopen(url_req)
	print('Downloading calender from %s. ' % url)

	data = []
	for line in data_obj:
		new_line = line.decode('utf-8')
		new_line = new_line.replace('null', '[]')
		new_line = new_line.replace('\n', '')
		data.append(new_line)
		if new_line == '  } ]':
			del(data_obj)
			break

	if data:
		data = ' '.join(data)
		data = ' '.join(data.split()) + ' }'
		data = ast.literal_eval(data)
	return(data)

def parse_data(last_ref, delta_thresh):
	database_keys = []
	delta_list = []
	dbs_list = []

	data = get_data()
	for key in data:
		database_keys.append(key)

	ref_time = data[database_keys[0]][0][ref_key]
	if last_ref != ref_time:
		print('%s: Data refreshed.' % str(datetime.now()))
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
	delta_dbs_list = []

	delta_list, ref_time = parse_data(last_ref, delta_thresh)

	if ref_time == last_ref:
		delta_list = past_delta_list
		delta_list_additions = []
	else:
		delta_list_additions = set(delta_list).difference(past_delta_list)
		for addition in delta_list_additions:
			if addition.split()[0] not in delta_dbs_list:
				delta_dbs_list.append(addition.split()[0])

	dat_timer = Timer(data_update_timer, update_list, [delta_list, delta_thresh, ref_time])
	dat_timer.start()

	if delta_list_additions:
		compose_message(delta_list_additions, delta_dbs_list)
	return(msg, att)

def conv_delta_time(delta_string):
	if delta_string:
		delta_string = delta_string.split()
		if len(delta_string) == 1:
			delta_string.insert(0, '0')
		else:
			del(delta_string[1])
		delta_array = list(map(int, ' '.join(' '.join(delta_string).split(':')).split()))
		delta_time = timedelta(days = delta_array[0], hours = delta_array[1], minutes = delta_array[2], seconds = delta_array[3])

	else:
		delta_time = []

	return(delta_time)

def compose_message(delta_list_additions, delta_dbs_list):
	att = []
	msg = 'Latency Alerts!'
	for dbs in delta_dbs_list:
		value_str = ''
		i = 0
		for delta in delta_list_additions:
			if delta.split()[0] == dbs:
				value_str += ' '.join(delta.split()[1:]) + '\n'
				i += 1
		if i < 5:
			color_code = colors[0]
		elif i < 10:
			color_code = colors[1]
		else:
			color_code = colors[2]
		# Attachment template for upcoming events
		att_temp = {
				'color': color_code,
				'author_name': dbs,
				'text': value_str,
		}
		att.append(att_temp)
	return(msg, att)


def clean_str(value, key = 'default'):
	if value:
		value = value.replace('-',' ')
		if key not in ('commit', 'commitid', 'status'):
			value = list(value)
			value[0] = value[0].upper()
			value = ''.join(value)
	return value

def clean_arr(data):
	for index, value in enumerate(data):
		if type(value) == str:
			data[index] = clean_str(value)
		elif type(value) == dict:
			clean_dict(value)
		elif type(value) == list:
			clean_arr(value)

# A function that cleans strings in a given dictionary
def clean_dict(data):
	for key, value in data.items():
		if type(value) == dict:
			clean_dict(value)
		elif type(value) == str:
			data[key] = clean_str(value, key)
		elif type(value) == list:
			clean_arr(value)
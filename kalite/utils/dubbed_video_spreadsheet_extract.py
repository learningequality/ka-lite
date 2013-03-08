# This script reads from the static/data/dubbedvideoslist.xlsx provided by Khan Academy 
# and maps english video ids to the video id of the language
# 
# it will output a json file in the following format 
# E.g. 
# { 
#	"Foreign Language Code": 
# 	{
#		"Foreign Language Video ID": "English Video ID"
#	}, etc.
# }

# Library for reading xlsx files 
import xlrd
import pdb

def map_dubbed_ids(path_to_xlsx, sheet_name):
	language_codes = {
		"ARABIC": "ar",
		"ARMENIAN": "hy",
		"BAHASA INDONESIA": "id",
		"BANGLA": "bn",
		"BULGARIAN": "bg",
		"CZECH": "cs",
		"DANISH": "da",
		"DEUTSCH": "de",
		"ESPANOL": "es",
		"FARSI": "fa",
		"FRANCAIS": "fr",
		"GREEK": "el",
		"HEBREW": "he",
		"ITALIANO": "it",
		"KISWAHILI": "sw",
		"KOREAN": "ko",
		"MANDARIN": "zn",
		"NORSK": "nn",
		"POLISH": "pl",
		"PORTUGUES": "pt_BR",
		"RUSSIAN": "ru",
		"THAI": "th",
		"TURKCE": "tr",
		"UKRAINIAN": "uk",
		"URDU": "ur",
		"XHOSA": "xh" 
	}
	spreadsheet = xlrd.open_workbook(path_to_xlsx)
	worksheet = spreadsheet.sheet_by_name(sheet_name)
	ncolumns = worksheet.ncols - 1
	nrows = worksheet.nrows - 1
	categories = worksheet.row_values(5)
	language_column_start = 11
	data_row_start = 5

	# List of Languages
	languages = [] 
	for i in range(language_column_start, ncolumns):
		languages.append(worksheet.cell_value(data_row_start, i))
	
	# List of language codes
	coded_categories = []
	for i in range(0, len(languages)-1):
		coded_categories.append(language_codes[languages[i]])
	
	# Create parent level by indexing through all languages
	final_map = {}
	for code in coded_categories:
		final_map[code] = {}

	# Create second level
	for key, value in final_map.iteritems():
		for i in range(6, nrows):
			# value[worksheet.cell_value(i, 9)] = {
			# 	# "serial": worksheet.cell_value(i, 0),
			# 	# "date_added": worksheet.cell_value(i, 1),
			# 	# "date_created": worksheet.cell_value(i, 2),
			# 	# "english_title": worksheet.cell_value(i, 3),
			# 	# "english_subject": worksheet.cell_value(i, 4),
			# 	# "english_topic": worksheet.cell_value(i, 5),
			# 	# "english_subtopic": worksheet.cell_value(i, 6),
			# 	# "english_tutorial": worksheet.cell_value(i, 7),
			# 	# "titled_id": worksheet.cell_value(i, 8),
			# 	# "english_youtubeids": worksheet.cell_value(i, 9),
			# 	# "professsionally_subtitled": worksheet.cell_value(i, 10),
			# 	# "dubbed_youtubeid": worksheet.cell_value(i, categories.index(key))
			# 	"english_title": worksheet.cell_value(i, 3),
			# 	"dubbed_youtubeid": worksheet.cell_value(i, categories.index(key))
			# }
			value[worksheet.cell_value(i, coded_categories.index(key)+11)] = worksheet.cell_value(i, 9)
	return final_map

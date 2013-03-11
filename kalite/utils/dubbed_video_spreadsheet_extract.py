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
	language_column_start = 11
	language_row = 5
	row_data_begins = 6
	english_mapping_col = 9
	all_categories = worksheet.row_values(5)
	all_categories_string = " ".join(all_categories)
	print "Path to Spreadsheet: %s\nSheet Name: %s\n# Columns: %d\n# Rows: %d\nAll Categories: %s" % (path_to_xlsx, sheet_name, ncolumns, nrows, all_categories_string)

	# List of Languages
	languages = [] 
	for i in range(language_column_start, ncolumns):
		languages.append(worksheet.cell_value(language_row, i))
	# print "All languages: %s\nLength: %d" % ((", ".join(languages)), len(languages))
	
	# List of language codes
	coded_categories = []
	for lang in languages:
		coded_categories.append(language_codes[lang])
	# print "Language codes: %s\nLength: %d" % ((", ".join(coded_categories)), len(coded_categories))
	
	# Create parent level by indexing through all languages
	final_map = {}
	for code in coded_categories:
		final_map[code] = {}
	# print "Final map keys length %s..." % (len(final_map.keys()))

	# Create second level
	n = 0
	for key, value in final_map.iteritems():
		# print "Extracting %d. %s..." % (n, key)
		n += 1
		for i in range(row_data_begins, nrows):
			value[worksheet.cell_value(i, coded_categories.index(key)+language_column_start)] = worksheet.cell_value(i, english_mapping_col)
	
	print "\nSuccessfully extracted language mapping data from spreadsheet.\n" 
	return final_map

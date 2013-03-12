"""
This script returns 

"""
import optparse
import logging



def setup_logging():
	logging.basicConfig(level=logging.INFO,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def main():
	"""Handles command line args directs the script"""
	parser = optparse.OptionParser()

	parser.add_option("-U", "--update", action="store_true", dest="update", 
		help="Request updated data on language channels via the YouTube API.",
		default=False)

	parser.add_option("-l", "--language-channel", action="append", dest="language_channels",
		help="Languages to update and write to CSV (if CSV flag is added). Default is all.",
		default=[])

	parser.add_option("--csv", action="store_true", dest="generate_csv",
		help="Write CSV files summarizing statistics for videos on language channels.")

	parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
		help="Suppress output to file. Default is to write to both console and file."
		default=False)

	options, args = parser.parse_args()

	if options.quiet:
		setup_logging() 

	if options.update:
		if not language_channels:
			# TODO
			update_all_language_channels_json()
		else:
			for language in language_channels:
				# TODO
				update_language_channel_json(language)

	if options.generate_csv:
		if not language_channels:
			# TODO
			create_inclusive_csvs(options.generate_csv.value)
		else:
			# TODO
			create_specific_csvs(options.generate_csv.value, language_channels)

	#TODO
	return video_ids_set(language_channels)


if __name__ == '__main__':
	main()
# data file names, file paths, and headers
import os
import logging

headers = {
    # "X-api-username": "kalite",
    # "X-apikey": "9931eb077687297823e8a23fd6c2bfafae25c543",
    "X-api-username": "dyl",
    "X-apikey": "6a7e0af81ce95d6b810761041b72412043851804",
}

data_path = os.path.dirname(os.path.realpath(
    __file__)) + "/../../static/data/subtitledata/"

logger = logging.getLogger('central/utils')

api_info_filename = "srts_api_info.json"

language_srt_map = "language_srts_map.json"

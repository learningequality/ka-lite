import json
import os

with open(os.path.join(os.path.dirname(__file__), "facility_unit_mappings.json")) as f:
    CONDITION_BY_FACILITY_AND_UNIT = json.load(f)

with open(os.path.join(os.path.dirname(__file__), "facility_grade_mappings.json")) as f:
    GRADE_BY_FACILITY = json.load(f)

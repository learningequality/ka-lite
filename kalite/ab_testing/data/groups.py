import json
import os


with open(os.path.join(os.path.dirname(__file__), "facility_grade_mappings.json")) as f:
    GRADE_BY_FACILITY = json.load(f)


def get_grade_by_facility(facility):
    return GRADE_BY_FACILITY.get(facility.id, GRADE_BY_FACILITY.get(facility.name, GRADE_BY_FACILITY.get(facility.id[0:8], 0)))
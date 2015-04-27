import json
import os

with open(os.path.join(os.path.dirname(__file__), "facility_unit_mappings.json")) as f:
    CONDITION_BY_FACILITY_AND_UNIT = json.load(f)

with open(os.path.join(os.path.dirname(__file__), "facility_grade_mappings.json")) as f:
    GRADE_BY_FACILITY = json.load(f)

def get_condition_by_facility_and_unit(facility, unit):
    return CONDITION_BY_FACILITY_AND_UNIT.get(facility.id, CONDITION_BY_FACILITY_AND_UNIT.get(facility.name, CONDITION_BY_FACILITY_AND_UNIT.get(facility.id[0:8], {}))).get(str(unit), "")

def get_grade_by_facility(facility):
    return GRADE_BY_FACILITY.get(facility.id, GRADE_BY_FACILITY.get(facility.name, GRADE_BY_FACILITY.get(facility.id[0:8], 0)))
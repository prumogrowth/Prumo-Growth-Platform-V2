"""Failing lab assertions must not echo the very material they detect."""
def reject_material(data,values):
    if any(value.encode() in data for value in values if value):
        raise AssertionError('I84_MATERIAL_MATCH_WITHHELD')

# debug_script.py
from utc_actions import *

if __name__ == "__main__":
    # updatePickledMeetingMinutesForMeetingRange(181)
    m = fetchMinutesForMeetingRange(86,89)
    a86 = findTaggedActionsInMinutes(m[86])
    a87 = findTaggedActionsInMinutes(m[87])
    a88 = findTaggedActionsInMinutes(m[88])
    a89 = findTaggedActionsInMinutes(m[89])
    pass

    
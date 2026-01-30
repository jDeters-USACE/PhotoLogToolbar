import os
import time
from datetime import datetime
from tzlocal import get_localzone # $ pip install tzlocal

path = r'R:\Code\ArcMap Extensions\Photo-LogToolbar\Test Projects\201500644 - Stewart Water Diversion\2016-06-14 - Site Visit\Photographs\DSCN0535.jpg'
local_timezone = get_localzone()
aware_dt = datetime.fromtimestamp(os.path.getctime(path), local_timezone)
print(aware_dt)


modified_time = os.path.getctime(path)
mtime_obj1 = datetime(*time.localtime(modified_time)[:6])
print(mtime_obj1.strftime('%Y-%m-%d_%H-%M-%S'))
# (or)
mtime_obj2 = datetime.fromtimestamp(modified_time)
print(mtime_obj2.strftime('%Y-%m-%d_%H-%M-%S'))

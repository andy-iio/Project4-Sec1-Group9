from database import Database  

import os
if os.path.exists('preppersdb.sqlite'):
    os.rename('preppersdb.sqlite', 'preppersdb.sqlite.backup')
    
db = Database()
print("done")
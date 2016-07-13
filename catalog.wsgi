#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
app_path = "/var/www/catalog"
if not app_path in sys.path:
    sys.path.insert(0, app_path)

from project import app as application
application.secret_key = 'Add your secret key'
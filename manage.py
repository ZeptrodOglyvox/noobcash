from flask_script import Manager
from backend import create_app

m = Manager(create_app(port=5000, app_id=0))


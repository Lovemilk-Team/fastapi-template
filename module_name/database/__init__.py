from .structs import *  # load SQL models, don't remove
from .connector import *

engine = connect2database()
dbsession_depend = get_dbsession_depend(engine)

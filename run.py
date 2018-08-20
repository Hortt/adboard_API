from api import app
from api import config

app.run(debug=config.debug)

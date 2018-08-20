from flask import Flask
from api.views import mod

app = Flask(__name__)
app.register_blueprint(views.mod)

if __name__ == '__main__':
    app.run(debug=True)

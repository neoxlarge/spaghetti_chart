#flask test
import flask

app = flask.Flask(__name__)

@app.route("/ddd")
def hello():
    return "hello"

app.run()
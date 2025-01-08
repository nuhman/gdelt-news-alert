from gdeltdoc import GdeltDoc, Filters
import pandas as pd
import time
from flask import Flask, render_template, Response
import json

app = Flask(__name__)

@app.route("/")
def users():
    all_users = [
        {'username': 'Tendulkar'},
        {'username': 'Federrer'},
        {'username': 'Modirc'}
    ]
    return Response(json.dumps(all_users), mimetype='application/json')

if __name__ == "__main__":
    app.run(debug=True)
    
    
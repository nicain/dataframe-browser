from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__, template_folder='.')

@app.route('/')
def hello_world():
    return 'Hello, World!'

data = {'active':None}

@app.route("/active", methods=['GET', 'POST'])
def show_tables():


    if request.method == 'POST': 
        data['active'] = request.form['data']
        # data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'tests', 'example.csv'))


    return render_template('view.html', table=data['active'])


if __name__ == "__main__":
    app.run(debug=True)
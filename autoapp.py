from flask import Flask, render_template, request
import pandas as pd
import os
import json
from flask_socketio import SocketIO 

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app) 

@app.route('/')
def hello_world():
    return 'Hello, World!'

# Achieves persistence:
data = {'active':None}

@app.route("/graph", methods=['GET'])
def graph():

    return render_template('graph.html')

@app.route("/active", methods=['GET', 'POST'])
def active():


    if request.method == 'POST': 
        data['active'] = (request.form['data'], request.form['header'], request.form['table_id'])

    return render_template('view.html', table_id=data['active'][2], table=data['active'][0], header=data['active'][1])

@app.route("/multi", methods=['GET']) 
def multi():  
    return render_template('multi.html', uuid_table_list=data['active'], header='') 

@app.route("/model", methods=['POST']) 
def model(): 
 
    uuid_table_list = json.loads(request.json) 
    data['active'] = uuid_table_list 
 
    socketio.emit('reload') 

    return json.dumps(True)


@app.route('/background_process_test')
def background_process_test():
    print "Hello"
    return json.dumps({"nothing":'much'})

if __name__ == "__main__":
    app.run(debug=True)
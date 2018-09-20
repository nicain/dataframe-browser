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

@app.route("/reload", methods=['POST']) 
def reload(): 
    socketio.emit('reload') 
    return json.dumps(True)


@app.route('/background_process_test')
def background_process_test():
    return json.dumps({"nothing":'much'})

@app.route('/graph', methods=['POST'])
def graph_post():
    graph_dict = json.loads(request.json) 
    data['graph'] = graph_dict
    return json.dumps(True)

@app.route('/graph', methods=['GET'])
def graph_get():
    return render_template('graph.html', uuid_table_list=data['graph'], header='') 

@app.route('/graph_json')
def graph_json():
    return json.dumps(data['graph'])

from dataframe_browser.mappers import mapper_library_dict

@app.route('/lazy_formatting', methods=['POST'])
def lazy_formatting():
    # return json.dumps(request.json)
    data = request.json
    result = mapper_library_dict[data['mapper_library']][data['mapper']](*data.get('args',[]), **data.get('kwargs', {}))
    return json.dumps({'result':result})

@app.route('/sandbox')
def sandbox():
    return render_template('sandbox.html') 

@app.route('/sandbox2', methods=['POST'])
def sandbox2():
    return json.dumps({'a':'a'})

if __name__ == "__main__":
    app.run(debug=True)


    # {'mapper':'nwb_file_to_max_projection', 
    # 'mapper_library':'dataframe_browser.mappers.brain_observatory', 
    # 'args':['/allen/programs/braintv/production/neuralcoding/prod31/specimen_602810529/ophys_session_617204394/ophys_experiment_617388117/617388117.nwb']}
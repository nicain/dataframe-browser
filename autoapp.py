from flask import Flask, render_template, request, flash, redirect
import pandas as pd
import os
import json
from flask_socketio import SocketIO 
from dataframe_browser.dataframebrowser import DataFrameBrowser
from dataframe_browser.utilities import one


app = Flask(__name__, template_folder='.')
app.secret_key = 'super secret key'
socketio = SocketIO(app) 

dfb = DataFrameBrowser()

@app.route("/browser", methods=['GET']) 
def browser_get():  

    uuid_table_list = dfb.view.display_node()
    uuid_table_list_frame_index = [[fi]+list(f) for fi, f in enumerate(uuid_table_list)]

    return render_template('browser.html', uuid_table_list=uuid_table_list_frame_index, header='', disable_nav_parent_back=str(dfb.model.disable_nav_parent_back).lower())

@app.route("/bookmarks", methods=['POST'])
def bookmarks():

    print dict(request.form)
    print dfb.model.bookmarks

    return redirect('/sandbox')

@app.route("/command", methods=['POST'])
def cmd_post():

    if not request.json:
        data = dict(request.form)
        command = one(data.pop('command'))
        reload_bool = False
        redirect_to_main = True

    else:
        data = json.loads(request.json)
        command = data.pop('command')
        reload_bool = data.pop('reload', True)
        redirect_to_main = False

    if command == 'read':
        dfb.read(**data)
    elif command == 'open':
        dfb.open(**data)
    elif command == 'groupby':
        dfb.groupby(**data)
    elif command == 'groupfold':
        dfb.groupfold(**data)
    elif command == 'query':
        dfb.query(**data)
    elif command == 'drop':
        dfb.drop(**data)
    elif command == 'keep':
        dfb.keep(**data)
    elif command == 'concat':
        dfb.concat(**data)
    elif command == 'apply':
        dfb.apply(**data)
    elif command == 'back':
        dfb.back(**data)
    elif command == 'bookmark':
        dfb.bookmark(**data)
    elif command == 'reload':
        reload_bool = True
    else:
        print 'COMMAND NOT RECOGNIZED', command, reload_bool, data
        return json.dumps(True)    

    if reload_bool:
        socketio.emit('reload')
    
    if redirect_to_main:
        return redirect('/browser')
    else:
        return json.dumps(True)

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
    data = request.json
    result = mapper_library_dict[data['mapper']](*data.get('args',[]), **data.get('kwargs', {}))
    return json.dumps({'result':result})

@app.route('/sandbox')
def sandbox():
    return render_template('sandbox.html') 

@app.route('/sandbox2', methods=['POST'])
def sandbox2():
    print dict(request.form)
    return json.dumps(dict(request.form))

if __name__ == "__main__":
    
    import webbrowser

    webbrowser.open('http://localhost:5000/browser')
    
    app.run(debug=True)




    # {'mapper':'nwb_file_to_max_projection', 
    # 'mapper_library':'dataframe_browser.mappers.brain_observatory', 
    # 'args':['/allen/programs/braintv/production/neuralcoding/prod31/specimen_602810529/ophys_session_617204394/ophys_experiment_617388117/617388117.nwb']}
from flask import Flask, render_template, request, flash, redirect, session, url_for, escape
import pandas as pd
import os
import json
from flask_socketio import SocketIO 
from dataframe_browser.dataframebrowser import DataFrameBrowser
from dataframe_browser.utilities import one, generate_uuid
import traceback



app = Flask(__name__, template_folder='.')
app.secret_key = 'super secret key'
socketio = SocketIO(app) 

dfb_dict = {}


@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         session['username'] = request.form['username']
#         return redirect('/browser')
#     return '''
#         <form method="post">
#             <p><input type=text name=username>
#             <p><input type=submit value=Login>
#         </form>
#     '''

# @app.route('/logout')
# def logout():
#     # remove the username from the session if it's there
#     session.pop('username', None)
#     return redirect('/browser')

@app.route("/browser") 
def browser_base():

    session_uuid = generate_uuid()
    session['uuid'] = session_uuid
    dfb_dict[session_uuid] = DataFrameBrowser(session_uuid=session_uuid)

    return redirect('/browser/{session_uuid}'.format(session_uuid=session_uuid))

@app.route("/browser/<session_uuid>", methods=['GET']) 
def browser_get(session_uuid):  

    dfb = dfb_dict[session_uuid]

    # TODO: Protect with Try excetp that flashes error message
    try:

        uuid_table_list = dfb.view.display_node()
        uuid_table_list_frame_index = [[fi]+list(f) for fi, f in enumerate(uuid_table_list)]

        if dfb.model.active.name is None:
            active_name_str = ''
        else:
            active_name_str = dfb.model.active.name

        return render_template('browser.html', 
                            uuid_table_list=uuid_table_list_frame_index, 
                            header='', # TODO: might remove this
                            disable_nav_parent_back = str(dfb.model.active_is_root).lower(),
                            disable_nav_child_forward = str(dfb.model.active_is_leaf).lower(),
                            disable_nav_bookmark_button = str(dfb.model.active_is_bookmarked or dfb.model.active==dfb.model.root).lower(),
                            active_name_str=active_name_str,
                            groupable_columns_dict=dfb.model.groupable_columns_dict,
                            disable_groupby_menu_button=str(not dfb.model.groupable_state).lower(),
                            disable_concatenate_menu_button=str(not dfb.model.can_concatenate).lower(),
                            all_active_columns=dfb.model.all_active_columns,
                            mapper_list=dfb.mapper_library_dict.keys(),
                            disable_fold_menu_button=str(not dfb.model.foldable_state).lower(),
                            all_index_columns=dfb.model.all_index_columns,
                            disable_transpose_menu_button=str(not len(dfb.model.all_index_columns)>0).lower(),
                            session_uuid=session_uuid,)
    
    except Exception as e:

        # TODO: Make error read, include support message:
        flash('ERROR: %s' % str(e.message), category='warning')
        traceback.print_exc()
        dfb.model.set_active(dfb.model.root)
        return render_template('browser.html')

@app.route("/active/<ii>", methods=['POST', 'GET']) 
def get_active_ii(ii):
    raise Exception('BROKEN')
    return dfb.active.node_frames[int(ii)].df.to_json()

@app.route("/active", methods=['POST', 'GET']) 
def get_active():
    raise Exception('BROKEN')
    return json.dumps({str(ii):dfb.active.node_frames[int(ii)].df.to_dict() for ii in range(len(dfb.active.node_frames))})

@app.route("/bookmarks", methods=['POST'])
def bookmarks():

    print dict(request.form)
    print dfb.model.bookmarks

    return redirect('/sandbox')

@app.route("/command/<session_uuid>", methods=['POST'])
def cmd_post(session_uuid):

    dfb = dfb_dict[session_uuid]

    try:

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
        elif command == 'fold':
            dfb.fold(**data)
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
        elif command == 'forward':
            dfb.forward(**data)
        elif command == 'bookmark':
            dfb.bookmark(**data)
        elif command == 'transpose':
            dfb.transpose(**data)
        elif command == 'reload':
            reload_bool = True
        else:
            raise Exception('COMMAND NOT RECOGNIZED: %s' % command)

        if reload_bool:
            socketio.emit('reload')
        
        if redirect_to_main:
            return redirect('/browser/{session_uuid}'.format(session_uuid=session_uuid))
        else:
            return json.dumps(True)
    
    except Exception as e:

        # TODO: Make error read, include support message: MOVE BUTTON TO LEFT
        flash('ERROR: %s' % str(e.message), category='warning')

        traceback.print_exc()

        return redirect('/browser/{session_uuid}'.format(session_uuid=session_uuid))
        # return render_template('browser.html')

# @app.route("/multi", methods=['GET']) 
# def multi():  
#     return render_template('multi.html', uuid_table_list=data['active'], header='') 

# @app.route("/model", methods=['POST']) 
# def model(): 
 
#     uuid_table_list = json.loads(request.json) 
#     data['active'] = uuid_table_list 
 
#     socketio.emit('reload') 

#     return json.dumps(True)

# @app.route("/reload", methods=['POST']) 
# def reload(): 
#     socketio.emit('reload') 
#     return json.dumps(True)


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

# @app.route('/graph_json')
# def graph_json():
#     return json.dumps(data['graph'])



@app.route('/lazy_formatting/<session_uuid>', methods=['POST'])
def lazy_formatting(session_uuid):
    dfb = dfb_dict[session_uuid]
    data = request.json
    result = dfb.mapper_library_dict[data['mapper']](*data.get('args',[]), **data.get('kwargs', {}))
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
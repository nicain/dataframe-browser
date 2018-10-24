from flask import Flask, render_template, request, flash, redirect, session, url_for, escape
from werkzeug.utils import secure_filename
import pandas as pd
import os
import json
from flask_socketio import SocketIO 
from dataframe_browser.dataframebrowser import DataFrameBrowser
from dataframe_browser.utilities import one, generate_uuid
import dataframe_browser
import traceback
from dataframe_browser.mappers import mapper_library_dict
import pgpasslib
import io
import dill
import urlparse


ALLOWED_EXTENSIONS = ['csv', 'p', 'pkl', 'xls', 'xlsx']
UPLOAD_FOLDER = '/home/nicholasc/tmp/upload'
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
socketio = SocketIO(app) 

dfb_dict = {}

lims_password = pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader')

def render_node(curr_node, session_uuid, disable_nav_bookmark_button):

    uuid_table_list = curr_node.get_table_list(page_length=None, session_uuid=session_uuid)
    active_name_str = curr_node.name if curr_node.name is not None else ''

    if curr_node.uuid in request.url:
        permalink = request.url
    else:
        permalink = urlparse.urljoin(request.url, curr_node.uuid)

    return render_template('browser.html', 
                        uuid_table_list=uuid_table_list, 
                        disable_nav_parent_back = str(curr_node.parent is None).lower(),
                        disable_nav_child_forward = str(len(curr_node.children) == 0).lower(),
                        disable_nav_bookmark_button = disable_nav_bookmark_button,
                        active_name_str=active_name_str,
                        groupable_columns_dict=curr_node.groupable_columns_dict,
                        disable_groupby_menu_button=str(not curr_node.groupable_state).lower(),
                        disable_concatenate_menu_button=str(not curr_node.can_concatenate).lower(),
                        columns=curr_node.common_columns,
                        mapper_list=mapper_library_dict.keys(), # TODO get from an endpoint from CORS lazy_loader service
                        disable_fold_menu_button=str(not curr_node.foldable_state).lower(),
                        all_index_columns=curr_node.index_columns,
                        disable_transpose_menu_button=str(not len(curr_node.index_columns)>0).lower(),
                        session_uuid=session_uuid,
                        version=dataframe_browser.__version__,
                        lims_password=lims_password,
                        upload_folder=app.config['UPLOAD_FOLDER'],
                        permalink=permalink)

def render_browser(dfb_dict, session_uuid, node_uuid_or_bookmark=None):

    dfb = dfb_dict[session_uuid]

    if node_uuid_or_bookmark is None:
        curr_node = dfb.model.active
    else:
        if node_uuid_or_bookmark in dfb.model.bookmarks:
            curr_node = dfb.model.bookmark_dict[node_uuid_or_bookmark]
        else:
            curr_node =  one([n for n in dfb.model.nodes if n.uuid == node_uuid_or_bookmark])

    disable_nav_bookmark_button = str(curr_node in dfb.model.bookmarked_nodes or curr_node == dfb.model.root).lower()
    try:
        
        return render_node(curr_node, session_uuid, disable_nav_bookmark_button)
    
    except Exception as e:

        # TODO: Make error read, include support message:
        flash('ERROR: %s' % str(e.message), category='warning')
        traceback.print_exc()
        dfb.model.set_active(dfb.model.root)
        return render_template('browser.html', version=dataframe_browser.__version__, lims_password=lims_password)

@app.route('/')
def index():
    return render_template('index.html', version=dataframe_browser.__version__, lims_password=lims_password)

@app.route("/browser/") 
def browser_base():

    session_uuid = generate_uuid()
    session['uuid'] = session_uuid
    dfb_dict[session_uuid] = DataFrameBrowser(session_uuid=session_uuid)

    return redirect('/browser/{session_uuid}/'.format(session_uuid=session_uuid))

@app.route("/browser/<session_uuid>/", methods=['GET']) 
def browser_get(session_uuid):  

    return render_browser(dfb_dict, session_uuid)

@app.route("/browser/<session_uuid>/<node_uuid_or_bookmark>/", methods=['GET']) 
def browser_get_node(session_uuid, node_uuid_or_bookmark): 

    return render_browser(dfb_dict, session_uuid, node_uuid_or_bookmark=node_uuid_or_bookmark)
    

@app.route("/node_uuid/<session_uuid>/", methods=['GET']) 
def node_uuid(session_uuid):
    if dfb_dict[session_uuid].model.active.name is not None:
        return dfb_dict[session_uuid].model.active.name
    else:
        return dfb_dict[session_uuid].model.active.uuid


@app.route("/stable/<session_uuid>/<node_uuid>/<frame_index>/", methods=['GET']) 
def stable_get(session_uuid, node_uuid, frame_index):

    frame_index = int(frame_index)

    dfb = dfb_dict[session_uuid]    


    # print [n.uuid for n in dfb.model.nodes]
    node_uuid = [n.uuid for n in dfb.model.nodes][-1]
    # print dfb.view.display_node()
    # uuid_table_list_frame_index = [[fi]+list(f) for fi, f in enumerate(uuid_table_list)]
    # print uuid_table_list

    node =  one([n for n in dfb.model.nodes if n.uuid == node_uuid])
    # print
    table_html = node.node_frames[frame_index].to_html(interactive=False)

    return render_template('stable.html', table_html=table_html)

@app.route("/active/<session_uuid>/", methods=['POST', 'GET']) 
def get_active(session_uuid):

    dfb = dfb_dict[session_uuid]

    return json.dumps({str(ii):dfb.active.node_frames[int(ii)].df.to_dict() for ii in range(len(dfb.active.node_frames))})

@app.route("/active_uuid/", methods=['POST', 'GET']) 
def get_active_uuid():

    session_uuid = json.loads(request.json)['session_uuid']
    dfb = dfb_dict[session_uuid]

    return json.dumps({'active_uuid':dfb.model.active.uuid})

@app.route("/upload_folder/", methods=['POST', 'GET']) 
def get_upload_folder():

    return json.dumps({'upload_folder':app.config['UPLOAD_FOLDER']})

@app.route("/bookmarks/", methods=['POST'])
def bookmarks():

    print dict(request.form)
    print dfb.model.bookmarks

    return redirect('/sandbox')

@app.route("/command/<session_uuid>/", methods=['POST'])
def cmd_post(session_uuid):

    # When the client cursor connects for the first time, initialize a session:
    if session_uuid not in dfb_dict:
        dfb_dict[session_uuid] = DataFrameBrowser(session_uuid=session_uuid)

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
            if isinstance(data['filename'], (list, tuple)) and str(os.path.dirname(one(data['filename']))) == str(app.config['UPLOAD_FOLDER']):
                flash('File uploaded: {filename}'.format(filename=os.path.basename(one(data['filename']))), category='info')
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
        elif command == 'mapper':
            dfb.mapper(**data)
        elif command == 'reload':
            reload_bool = True
        else:
            raise Exception('COMMAND NOT RECOGNIZED: %s' % command)

        if reload_bool:
            socketio.emit('reload')
        
        if redirect_to_main:
            return redirect('/browser/{session_uuid}/'.format(session_uuid=session_uuid))
        else:
            return json.dumps(True)
    
    except Exception as e:

        # TODO: Make error read, include support message: MOVE BUTTON TO LEFT
        flash('ERROR: %s' % str(e.message), category='warning')

        traceback.print_exc()

        return redirect('/browser/{session_uuid}/'.format(session_uuid=session_uuid))


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


@app.route('/lazy_formatting/<session_uuid>', methods=['POST'])
def lazy_formatting(session_uuid):
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

@app.route('/upload/<session_uuid>/', methods=['GET', 'POST'])
def upload_file(session_uuid):
    if request.method == 'POST':

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', category='error')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', category='danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect('/command/{session_uuid}/'.format(session_uuid=session_uuid), code=307)
        else:
            flash('Filename not allowed: {filename}'.format(filename=file.filename), category='danger')
            return redirect(request.url)

    return render_template('browser.html') 

@app.route('/cursor/')
def cursor():

    session_uuid = generate_uuid()
    dfb_dict[session_uuid] = DataFrameBrowser(session_uuid=session_uuid)

    return redirect(urlparse.urljoin(request.url, session_uuid))

@app.route('/cursor/<session_uuid>/')
def cursor_uuid(session_uuid):

    url_obj = urlparse.urlparse(request.url_root)

    cursor_file_name = os.path.join(os.path.dirname(__file__),'dataframe_browser', 'data', 'cursor.p')

    c = dill.load(open(cursor_file_name, 'r'))
    c.port = url_obj.port
    c.hostname = url_obj.hostname
    c.session_uuid = session_uuid=session_uuid

    buf = io.BytesIO()
    dill.dump(c, buf)

    return buf.getvalue()


if __name__ == "__main__":
    
    import webbrowser

    webbrowser.open('http://localhost:5000/browser')
    
    app.run(debug=True)




    # {'mapper':'nwb_file_to_max_projection', 
    # 'mapper_library':'dataframe_browser.mappers.brain_observatory', 
    # 'args':['/allen/programs/braintv/production/neuralcoding/prod31/specimen_602810529/ophys_session_617204394/ophys_experiment_617388117/617388117.nwb']}
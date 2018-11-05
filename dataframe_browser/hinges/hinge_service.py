from flask import Flask, request
import json
from flask_cors import CORS
import hashlib

app = Flask(__name__)
app.secret_key = 'super secret key'
CORS(app, resources={r'/lazy_formatting/*':{"origins": "http://nicholasc-ubuntu:*"}}, allow_headers=['Content-Type'])


class Hinge(object):

    def __init__(self, name=None, uuid=None):
        assert not name is None
        self.name = name
        self.button_html_list = []

    def get_menu_html(self):
        return '\n'.join(self.button_html_list)

button_html = \
'''
<form class="form-inline" action="/command/{session_uuid}/" method="POST">
    <input type="hidden" name='columns' value='{column_string}'>
    <input type="hidden" name='new_column' value='max_projection_image'>
    <input type="hidden" name='drop' value='false'>
    <input type="hidden" name='mapper' value='brain_observatory.nwb_file_to_max_projection'>
    <input type="hidden" name='command' value="apply">
    <button type="submit" class="w-100 btn btn-primary btn-sm mx-2 my-1">max_projection</button>
</form>'''.strip()

master_hinge_dict = {}

h_tmp = Hinge(name='BOb session')
master_hinge_dict['7fa00718647f4ebcaf42246eb36eb6b1'] = h_tmp

h_tmp.button_html_list.append(button_html)

@app.route('/<hinge_uuid>/', methods=['GET'])
def hinge_html(hinge_uuid):

    hinge = master_hinge_dict[hinge_uuid]

    return hinge.get_menu_html()

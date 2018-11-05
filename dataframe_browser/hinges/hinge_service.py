from flask import Flask, request
import json
from flask_cors import CORS
from jinja2 import Environment, BaseLoader
import hashlib

app = Flask(__name__)
app.secret_key = 'super secret key'
CORS(app, resources={r'/lazy_formatting/*':{"origins": "http://nicholasc-ubuntu:*"}}, allow_headers=['Content-Type'])


button_template_str = \
'''
<form class="form-inline" action="/command/{session_uuid}/" method="POST">
    {% for name, value in hidden_name_value_dict.items() %}
    <input type="hidden" name={{name}} value={{value}}>
    {% endfor %}
    <button type="submit" class="w-100 btn btn-primary btn-sm mx-2 my-1">{{title}}</button>
</form>'''.strip()

class Hinge(object):

    button_template = Environment(loader=BaseLoader).from_string(button_template_str)
    
    def __init__(self, name=None, button_data_list=[]):
        assert not name is None

        self.name = name
        self.button_data_list = [x for x in button_data_list]

    def get_menu_html(self):
        menu_html_list = []
        for button_data in self.button_data_list:
            menu_html_list.append(Hinge.button_template.render(**button_data))
        return '\n'.join(menu_html_list)



h_tmp = Hinge(name='BOb session', button_data_list=[{'title':'HW', 
                                                     'hidden_name_value_dict':{'columns':"{column_string}",
                                                                               "new_column":"max_projection_image",
                                                                               "drop":"false",
                                                                               "mapper":"brain_observatory.nwb_file_to_max_projection",
                                                                               "command":"apply"}}])


master_hinge_dict = {}
master_hinge_dict['7fa00718647f4ebcaf42246eb36eb6b1'] = h_tmp

@app.route('/<hinge_uuid>/', methods=['GET'])
def hinge_html(hinge_uuid):

    hinge = master_hinge_dict[hinge_uuid]

    return hinge.get_menu_html()

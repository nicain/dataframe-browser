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

        self.name = name
        self.button_data_list = [x for x in button_data_list]

    def get_menu_html(self):
        menu_html_list = []
        for button_data in self.button_data_list:
            menu_html_list.append(Hinge.button_template.render(**button_data))
        return '\n'.join(menu_html_list)


master_hinge_dict = {}

h_1 = Hinge(name='nwb_file', button_data_list=[{'title':'max_projection', 
                                                     'hidden_name_value_dict':{'columns':"{column_string}",
                                                                               "new_column":"max_projection_image",
                                                                               "drop":"false",
                                                                               "mapper":"brain_observatory.nwb_file_to_max_projection",
                                                                               "command":"apply"}}])
master_hinge_dict['7fa00718647f4ebcaf42246eb36eb6b1'] = h_1

@app.route('/<hinge_uuid>/', methods=['GET', 'POST'])
def hinge_html(hinge_uuid):

    if request.method == 'POST':
        data = json.loads(request.json)
        name = data.get('name', None)
        if hinge_uuid in master_hinge_dict:
            hinge = master_hinge_dict[hinge_uuid]
        else:
            hinge = Hinge(name=name)
            master_hinge_dict[hinge_uuid] = hinge
        button_data = data.get('button_data', None)
        if not button_data['title'] in [x['title'] for x in hinge.button_data_list]:
            hinge.button_data_list.append(button_data)

        for curr_hinge_uuid, curr_hinge in master_hinge_dict.items():
            print curr_hinge_uuid, len(curr_hinge.button_data_list)

        return 'OK'

    
    elif request.method == 'GET':
        hinge = master_hinge_dict[hinge_uuid]
        return hinge.get_menu_html()



# master_hinge_dict['7fa00718647f4ebcaf42246eb36eb6b1'] = h_1


# h_merge = Hinge(name='merge', button_data_list=[{'title':'merge', 
#                                                          'hidden_name_value_dict':{'against':'/association/e78eb3a4589e4b1982b59efde517edd3/0/',
#                                                                                    "hinge_uuid":"33e6a0d43f4347f3bcc10c4a2659ba65",
#                                                                                    "command":"merge"}}])

# master_hinge_dict['33e6a0d43f4347f3bcc10c4a2659ba65'] = h_merge

# h_1 = Hinge(name='nwb_file', button_data_list=[{'title':'max_projection', 
                                                    #  'hidden_name_value_dict':{'columns':"{column_string}",
                                                    #                            "new_column":"max_projection_image",
                                                    #                            "drop":"false",
                                                    #                            "mapper":"brain_observatory.nwb_file_to_max_projection",
                                                    #                            "command":"apply"}}])


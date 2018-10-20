from flask import Flask, request
from dataframe_browser.mappers import mapper_library_dict
from dataframe_browser.cache import get_cache
import json
from flask_cors import CORS
import hashlib
import dill

r = get_cache(cache_type='redis')

app = Flask(__name__)
app.secret_key = 'super secret key'
CORS(app, resources={r'/lazy_formatting/*':{"origins": "http://nicholasc-ubuntu:*"}}, allow_headers=['Content-Type'])

@app.route('/lazy_formatting/<session_uuid>', methods=['POST'])
def lazy_formatting(session_uuid):
    data = request.json
    data_str = json.dumps(data, sort_keys=True)
    key = hashlib.md5(data_str).hexdigest()
    result = r[key]
    if not result:
        result = mapper_library_dict[data['mapper']](*data.get('args',[]), **data.get('kwargs', {}))
        r[key] = result
    return json.dumps({'result':result})

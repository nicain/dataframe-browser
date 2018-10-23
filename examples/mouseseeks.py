import pandas as pd
import requests
import dill
import requests

x = requests.get('http://nicholasc-ubuntu:5001/cursor/opc/')
c = dill.loads(x.content)
c.cell_width('90%')

df = pd.DataFrame(requests.get('http://mouse-seeks/cube/OpenScopePredictiveCoding/data').json()['data'])
c.upload(df)
c.display()
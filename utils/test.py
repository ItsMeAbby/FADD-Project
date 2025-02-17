import pandas as pd

import json
data= pd.read_json('standings.json')

print(data["team"].unique().tolist())
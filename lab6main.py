#/usr/bin/env python3


from flask import Flask, render_template
import getconfig
#import ospfconfig
#import diffconfig
#import migration

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getconfig')
def get_config():
    return getconfig.get_router_configs()

@app.route('/ospfconfig')
def configure_ospf():
    return ospfconfig.configure_all_routers()

@app.route('/diffconfig')
def compare_configs():
    return diffconfig.compare_all_configs()

@app.route('/migration')
def migrate():
    return migration.migrate_r4()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

#/usr/bin/env python3
from flask import Flask, render_template, send_from_directory, request
import getconfig
from ospfconfig import ospf_config, ospf_blueprint
#import migration
import os
from ping_loopbacks import ping_from_r1
from diffconfig import diff_blueprint



app = Flask(__name__)
app.register_blueprint(diff_blueprint)



CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
@app.route('/download/<filename>')
def download_config(filename):
    return send_from_directory(CONFIG_DIR, filename, as_attachment=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getconfig')
def get_config():
    return getconfig.get_router_configs()

@app.route('/ospfconfig', methods=['GET', 'POST'])
def configure_ospf():
    if request.method == 'POST':
        #debugging output for flask
        print("Received POST request on /ospfconfig")
        result = ospf_config()
        #debugging output for flask
        print(f"OSPF Result: {result}")  
        return result  # Show result in browser
    return render_template('ospf.html')

#app.register_blueprint(ospf_blueprint)
#app.register_blueprint(ping_blueprint)


@app.route('/diffconfig')
def compare_configs():
    return diffconfig.compare_all_configs()

@app.route('/ping')
def ping_page():
    results = ping_from_r1()  # Запускаем ping через функцию
    return render_template('ping.html', results=results)

@app.route('/migration')
def migrate():
    return migration.migrate_r4()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

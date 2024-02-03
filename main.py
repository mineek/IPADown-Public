import os
import json
from flask import Flask, request, jsonify, send_file, render_template
# make sure ipatoolpy can import reqs.* modules by adding the path to sys.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'ipatoolpy'))
from ipatoolpy.reqs.itunes import *
from ipatoolpy.reqs.store import *
# I don't know anymore, I cannot do python correctly, why does ipatoolpy not use if __name__ == '__main__'?
if not os.path.exists('libipatoolpy.py'):
    with open('ipatoolpy/main.py', 'r') as f:
        mainpy = f.read()
        search = """def main():
    tool = IPATool()

    tool.tool_main()

main()"""
        mainpy = mainpy.replace(search, "")
        with open('libipatoolpy.py', 'w') as f2:
            f2.write(mainpy)
from libipatoolpy import IPATool
import argparse
import logging
from rich.logging import RichHandler
from rich.console import Console
import rich
rich.get_console().file = sys.stderr

logging_handler = RichHandler(rich_tracebacks=True)
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[logging_handler]
)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logger = logging.getLogger('main')

app = Flask(__name__)
configjson = None
with open('config.json') as f:
    configjson = json.load(f)
appleidemail = configjson['appleid']
appleidpass = configjson['password']

@app.route('/download', methods=['POST'])
def download():
    ipaTool = IPATool()
    ipaTool.appId = request.form['appId']
    args = {
        "appleid": appleidemail,
        "password": appleidpass,
        "appId": ipaTool.appId,
        "purchase": True,
        "output_dir": "ipas",
        "downloadAllVersion": False,
        "appVerId": None,
        "itunes_server": "http://127.0.0.1:9000",
        "session_dir": None,
        "log_level": "info",
        "out_json": False
    }
    args = argparse.Namespace(**args)
    ipaTool.handleDownload(args)
    return send_file(ipaTool.jsonOut['downloadedIPA'], as_attachment=True)

@app.route('/downloadOlder', methods=['POST'])
def downloadOlder():
    ipaTool = IPATool()
    ipaTool.appId = request.form['appId']
    ipaTool.appVerId = request.form['appVerId']
    args = {
        "appleid": appleidemail,
        "password": appleidpass,
        "appId": ipaTool.appId,
        "purchase": True,
        "output_dir": "ipas",
        "downloadAllVersion": False,
        "appVerId": ipaTool.appVerId,
        "itunes_server": "http://127.0.0.1:9000",
        "session_dir": None,
        "log_level": "info",
        "out_json": False
    }
    args = argparse.Namespace(**args)
    ipaTool.handleDownload(args)
    return send_file(ipaTool.jsonOut['downloadedIPA'], as_attachment=True)

@app.route('/olderVersions', methods=['POST'])
def olderVersions():
    ipaTool = IPATool()
    ipaTool.appId = request.form['appId']
    args = {
        "appleid": appleidemail,
        "password": appleidpass,
        "appId": ipaTool.appId,
        "purchase": True,
        "output_dir": "ipas",
        "downloadAllVersion": False,
        "appVerId": None,
        "itunes_server": "http://127.0.0.1:9000",
        "session_dir": None,
        "log_level": "info",
        "out_json": True
    }
    args = argparse.Namespace(**args)
    ipaTool.handleHistoryVersion(args)
    return jsonify(ipaTool.jsonOut)

# Websocket server for log
from flask_socketio import SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

def logViaWS(msg):
    # don't log web requests
    if 'HTTP' in msg:
        return
    socketio.emit('log', msg)

@app.route('/ws', methods=['GET'])
def ws():
    return socketio.handle_request(request)

socketio.on_event('connect', lambda: logViaWS('Hello from server!'))
socketio.on_event('disconnect', lambda: print('Lost connection to client :('))

# pipe log to socketio
wsHandler = logging.StreamHandler()
wsHandler.setFormatter(logging.Formatter('%(message)s'))
wsHandler.emit = lambda record: logViaWS(record.getMessage())
logging.getLogger().addHandler(wsHandler)

# Start the web server
ssl = False
if os.path.exists('ssl/private.key') and os.path.exists('ssl/public.crt'):
    ssl = ('ssl/public.crt', 'ssl/private.key')
import threading
#threading.Thread(target=socketio.run, args=(app, '0.0.0.0', 9001)).start()
if ssl:
    threading.Thread(target=lambda: socketio.run(app, '0.0.0.0', 9001, ssl_context=ssl)).start()
else:
    threading.Thread(target=socketio.run, args=(app, '0.0.0.0', 9001)).start()

# Detect our local IP address
baseIP = None
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    baseIP = s.getsockname()[0]
    s.close()
except:
    print("Failed to get local IP address, exiting...")
    exit(1)

print(f"Local IP: {baseIP}")

useHTTPS = False
if ssl:
    useHTTPS = True
baseIP = f"https://{baseIP}" if useHTTPS else f"http://{baseIP}"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', baseIP=baseIP)

# for OTA itms-services
@app.route('/ota/<appId>/<appVerId>', methods=['GET'])
def ota(appId, appVerId):
    # look for the app in 'ipas' folder
    ipas = os.listdir('ipas')
    appName = None
    for ipa in ipas:
        if appId in ipa:
            appName = ipa
            break
    if not appName:
        return "App not found", 404
    # lookup app info
    ipaTool = IPATool()
    ipaTool.appId = appId
    args = {
        "appleid": appleidemail,
        "password": appleidpass,
        "appId": ipaTool.appId,
        "purchase": True,
        "output_dir": "ipas",
        "downloadAllVersion": False,
        "appVerId": None,
        "itunes_server": "http://127.0.0.1:9000",
        "session_dir": None,
        "log_level": "info",
        "out_json": True,
        "bundle_id": None,
        "country": "us",
        "get_verid": False
    }
    args = argparse.Namespace(**args)
    ipaTool.handleLookup(args)
    appInfo = ipaTool.jsonOut
    # create manifest
    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>items</key>
	<array>
		<dict>
			<key>assets</key>
			<array>
				<dict>
					<key>kind</key>
					<string>software-package</string>
					<key>url</key>
					<string>{baseIP}/ipas/{appName}</string>
				</dict>
			</array>
			<key>metadata</key>
			<dict>
				<key>bundle-identifier</key>
				<string>{appInfo['bundleId']}</string>
				<key>bundle-version</key>
                <string>{appVerId}</string>
				<key>kind</key>
				<string>software</string>
				<key>title</key>
				<string>MineekIPA</string>
			</dict>
		</dict>
	</array>
</dict>
</plist>
    """
    return manifest, 200, {'Content-Type': 'application/xml'}

@app.route('/ipas/<ipa>', methods=['GET'])
def ipas(ipa):
    if not os.path.exists(f'ipas/{ipa}'):
        return "IPA not found", 404
    return send_file(f'ipas/{ipa}', as_attachment=True)

if __name__ == '__main__':
    if ssl:
        app.run(host='0.0.0.0', port=443, ssl_context=ssl)
    else:
        app.run(host='0.0.0.0', port=80)
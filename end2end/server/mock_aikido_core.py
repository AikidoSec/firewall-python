import gzip

from flask import Flask, request, jsonify, Response
import sys
import os
import json
import time

app = Flask(__name__)

responses = {
    "config": {
        "receivedAnyStats": False,
        "success": True,
        "endpoints": [
            {
                "route": "/test_ratelimiting_1",
                "method": "*",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 2,
                    "windowSizeInMS": 1000 * 5,
                },
                "graphql": False,
            }
        ],
        "blockedUserIds": [],
    },
    "lists": {
        "success": True,
        "blockedIPAddresses": [
            {
                "source": "geoip",
                "description": "geo restrictions",
                "ips": ["1.2.3.4"]
            }
        ],
        "allowedIPAddresses": [],
        "blockedUserAgents": "",
    },
    "configUpdatedAt": {},
}

events = []


@app.route('/config', methods=['GET'])
def get_config():
    return jsonify(responses["configUpdatedAt"])


@app.route('/api/runtime/config', methods=['GET'])
def get_runtime_config():
    return jsonify(responses["config"])

@app.route('/api/runtime/firewall/lists', methods=['GET'])
def get_fw_lists():
    accept_encoding = request.headers.get('Accept-Encoding', '').lower()
    if 'gzip' not in accept_encoding:
        return jsonify({
            "success": False,
            "error": "Accept-Encoding header must include 'gzip' for firewall lists endpoint"
        }), 400

    json_data = json.dumps(responses["lists"])
    compressed_data = gzip.compress(json_data.encode('utf-8'))

    response = Response(compressed_data, content_type='application/json')
    response.headers['Content-Encoding'] = 'gzip'
    return response

@app.route('/api/runtime/events', methods=['POST'])
def post_events():
    print("Got event: ", request.get_json())
    if request.get_json():
        events.append(request.get_json())
    return jsonify(responses["config"])


@app.route('/mock/config', methods=['POST'])
def mock_set_config():
    configUpdatedAt = int(time.time())
    responses["config"] = request.get_json()
    responses["config"]["configUpdatedAt"] = configUpdatedAt
    responses["configUpdatedAt"] = { "serviceId": 1, "configUpdatedAt": configUpdatedAt }
    return jsonify({})


@app.route('/mock/events', methods=['GET'])
def mock_get_events():
    return jsonify(events)


@app.route('/mock/reset', methods=['GET'])
def mock_reset_events():
    events.clear()
    return jsonify({"msg": "OK"})


if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python mock_server.py <port> [config_file]")
        sys.exit(1)
    
    port = int(sys.argv[1])
    
    if len(sys.argv) == 3:
        config_file = sys.argv[2]
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as file:
                    configUpdatedAt = int(time.time())
                    responses["config"] = json.load(file)
                    responses["config"]["configUpdatedAt"] = configUpdatedAt
                    responses["configUpdatedAt"] = { "serviceId": 1, "configUpdatedAt": configUpdatedAt }
                    print(f"Loaded runtime config from {config_file}")
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {config_file}")
                sys.exit(1)
        else:
            print(f"Error: File {config_file} not found")
            sys.exit(1)
    
    app.run(host='0.0.0.0', port=port)

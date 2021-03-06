import os
from flask import Flask, request, render_template, abort, jsonify, make_response

class AutobuilderWebApp:
    """
    Flask web-application based for receiving hooks and providing a web-interface
    for monitoring current build status
    """
    def __init__(self, components):
        self.root = components

        self.app = Flask(
            __name__,
            static_url_path='/static',
            static_folder='../static',
            template_folder='../templates'
        )

        self.app.url_map.strict_slashes = False

    def routes(self):
        @self.app.route('/logs/<project>/<name>/<branch>', methods=['GET'])
        def global_logs(project, name, branch):
            '''
            collapse = "%s/%s/%s" % (project, name, branch)
            if not logs.get(collapse):
                abort(404)

            response = make_response(logs[collapse])
            response.headers["Content-Type"] = "text/plain"

            return response
            '''
            return "FIXME"

        @self.app.route('/report/<hash>', methods=['GET'])
        def global_commit_logs(hash):
            logfile = os.path.join(self.root.config['logs-directory'], "commits", hash)

            if not os.path.isfile(logfile):
                abort(404)

            with open(logfile, "r") as f:
                contents = f.read()

            response = make_response(contents)
            response.headers["Content-Type"] = "text/plain"

            return response

        @self.app.route('/build/status', methods=['GET'])
        def global_status():
            output = {}
            empty = ""

            for key, item in self.root.buildio.status.items():
                output[key] = {
                    'status': item['status'],
                    'name': item['name'],
                    'monitor': empty.join(item['console']),
                    'docker': item['docker'][0:10],
                    'started': item['started'],
                    'ended': item['ended'],
                    'error': item['error'],
                    'commits': item['commits'],
                    'artifact': item['artifact'],
                    'tag': item['tag'],
                }

            return jsonify(output)

        @self.app.route('/build/history/full', methods=['GET'])
        def global_history_full():
            return jsonify(self.root.buildio.backlog())

        @self.app.route('/build/history', methods=['GET'])
        def global_history():
            return jsonify(self.root.buildio.backlog(25))

        @self.app.route('/build/sync', methods=['GET'])
        def global_sync():
            self.root.buildio.live_current()
            self.root.buildio.live_history()
            return "OK"

        #
        # Git Hook
        #
        @self.app.route('/hook/kernel', methods=['GET', 'POST'])
        def build_hook():
            if not request.headers.get('X-Github-Event'):
                abort(400)

            payload = request.get_json()
            print(payload)

            if request.headers['X-Github-Event'] == "ping":
                print("[+] ping event")
                return self.root.initram.event_ping(payload)

            if request.headers['X-Github-Event'] == "push":
                print("[+] push event")
                return self.root.initram.event_push(payload)

            print("[-] unknown event: %s" % request.headers['X-Github-Event'])
            abort(400)

        #
        # Monitor page
        #
        @self.app.route("/monitor/", strict_slashes=False)
        def index():
            return render_template("index.html")

        @self.app.route("/", strict_slashes=False)
        def index_root():
            return render_template("index.html")

        #
        # flist
        #
        def monitor_bad_request(payload):
            response = jsonify(payload)
            response.status_code = 400
            return response

        @self.app.route(self.root.config['monitor-update-endpoint'], methods=['GET', 'POST'])
        def monitor_update():
            if not request.headers.get('X-Github-Event'):
                abort(400)

            payload = request.get_json()

            if request.headers['X-Github-Event'] == "ping":
                print("[+] update-endpoint: ping event for: %s" % payload["repository"]["full_name"])
                return "PONG"

            if request.headers['X-Github-Event'] == "push":
                print("[+] update-endpoint: push event")
                response = self.root.monitor.update(payload)

                if response['status'] == 'error':
                    return monitor_bad_request(response)

                return jsonify(response)

            print("[-] unknown event: %s" % request.headers['X-Github-Event'])
            abort(400)

        @self.app.route(self.root.config['repository-push-endpoint'], methods=['GET', 'POST'])
        def monitor_push():
            if not request.headers.get('X-Github-Event'):
                abort(400)

            payload = request.get_json()

            if request.headers['X-Github-Event'] == "ping":
                print("[+] push-endpoint: ping event for: %s" % payload["repository"]["full_name"])
                return "PONG"

            if request.headers['X-Github-Event'] == "push":
                print("[+] push-endpoint: push event")
                response = self.root.monitor.push(payload)

                if response['status'] == 'error':
                    return monitor_bad_request(response)

                return jsonify(response)

            print("[-] unknown event: %s" % request.headers['X-Github-Event'])
            abort(400)

    def serve(self):
        self.app.run(
            host=self.root.config['http-listen'],
            port=self.root.config['http-port'],
            debug=self.root.config['debug'],
            threaded=True,
            use_reloader=False
        )

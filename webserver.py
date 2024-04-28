import jwt
from jwt import PyJWKClient
import time 

from . import systemd
from flask import Flask, request, send_from_directory, Blueprint, Response, request
from . import settings
import os
from flask_cors import CORS
mon = systemd.ServiceMonitor("socksproxyman")
app = Flask(__name__)
api_blueprint = Blueprint('api', __name__)
CORS(app)
@api_blueprint.before_app_request
def before_request():
  if request.method == 'OPTIONS':
    resp = Response("")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers']= '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    return resp
  client_id = ''
  jwks_url = ''
  audience = ''
  issuer = ''
  try:
     settings.refresh_tunnels()
     setting= settings.get_settings()
     client_id = setting["client_id"]
     jwks_url = setting["jwks_url"]
     audience = setting["audience"]
     issuer = setting["issuer"]
     auth_control = settings.get_auth_control()
  except:
     settings.reconnect()
     settings.refresh_tunnels()
     setting= settings.get_settings()
     client_id = setting["client_id"]
     jwks_url = setting["jwks_url"]
     audience = setting["audience"]
     issuer = setting["issuer"]
     auth_control = settings.get_auth_control()
  if request.path == "/" or "favicon.ico" in request.path:
     return
  if not "api" in request.path.split("/")[0:-1][1]:
     return

  if auth_control[request.path.split("/")[0:-1][2]] == "public":
    return
  # Your API-specific logic here
  # (authentication, validation, etc.)
  if not request.headers.get('Authorization'):
    # Handle requests without Authorization header (e.g., log or reject)
    return {"status": "state.auth.fail"}, 401
  else:
    try:
      auth_result = False
      jwks_client = PyJWKClient(jwks_url)
      access_jwt = str(request.headers.get('Authorization'))
      signing_key = jwks_client.get_signing_key_from_jwt(access_jwt)
      token_decoded = jwt.decode(access_jwt, signing_key.key, algorithms=["RS256"], audience=audience, issuer=issuer)
      cid_check = False
      for cid in client_id.split(","):
         if (token_decoded["cid"]  == cid):
            cid_check = True
      if cid_check and not (int(time.time()) > int(token_decoded["exp"])):
          auth_result = True
    except:
      auth_result = False
    # Process requests with Authorization header
    # (e.g., extract token, validate credentials)
    if auth_result:
       pass

    else:
        return {"status": "state.auth.fail"}, 403
 
# Register the blueprint in your main app
app.register_blueprint(api_blueprint)

@app.route("/api/tunnels/list", methods=['GET'])
def list_tunnels():
    return settings.tunnels

@app.route("/api/tunnels/restart", methods=['POST'])
def restart_tunnels():
    os.system("systemctl --user restart socksproxyman.service")
    return {"status": "state.restarted"}

@app.route("/api/tunnels/start", methods=['POST'])
def start_tunnels():
    os.system("systemctl --user start socksproxyman.service")
    return {"status": "state.started"}

@app.route("/api/tunnels/stop", methods=['POST'])
def stop_tunnels():
    os.system("systemctl --user stop socksproxyman.service")
    return {"status": "state.stopped"}

@app.route("/api/tunnels/delete/<id>", methods=['POST'])
def delete_tunnel(id):
    result = settings.delete_tunnels(id)
    if result == "ok":
      return {"status": "state.tunnel.delete.deleted"}
    else:
      return {"status": "state.tunnel.delete.notfound"}, 400

@app.route("/api/tunnels/delete", methods=['POST'])
def delete_tunnel_without_id():
    return {"status": "state.tunnel.delete.notfound"}, 400

@app.route("/api/tunnels/delete/", methods=['POST'])
def delete_tunnel_without_id_with_slash():
    return {"status": "state.tunnel.delete.notfound"}, 400

@app.route("/api/tunnels/create/<id>", methods=['POST'])
def create_tunnel(id):
    data = request.get_json(silent=True)
    if(not data):
      return {"status": "state.tunnel.create.invalid.data"}, 400
    if(not data.get("host") or not data.get("target")):
      return {"status": "state.tunnel.create.invalid.data"}, 400
    else:
      for i in settings.tunnels:
         if i["name"] == id:
           return {"status": "state.tunnel.create.invalid.duplicate"}, 401
      settings.add_tunnels(id, data["host"], data["target"])
      return {"status": "state.tunnel.create.success"}

@app.route("/api/tunnels/create", methods=['POST'])
def create_tunnel_without_id():
    return {"status": "state.tunnel.create.invalid.data"}, 400

@app.route("/api/tunnels/create/", methods=['POST'])
def create_tunnel_without_id_with_slash():
    return {"status": "state.tunnel.create.invalid.data"}, 400

@app.route("/api/tunnels/edit/<id>", methods=['POST'])
def edit_tunnel(id):
    data = request.get_json(silent=True)
    if(not data):
      return {"status": "state.tunnel.edit.invalid.data"}, 400
    for i in settings.tunnels:
         if i["name"] == id:
           if data.get("name"):
             i["editname"] = data.get("name")
           i["host"] = data.get("host") or i["host"]
           i["target"] = data.get("target") or i["target"]
           i["edited"] = True
           settings.save()
           return {"status": "state.tunnel.edit.success"}
    return {"status": "state.tunnel.edit.invalid.notfound"}, 401

@app.route("/api/tunnels/edit", methods=['POST'])
def edit_tunnel_without_id():
    return {"status": "state.tunnel.edit.invalid.data"}, 400

@app.route("/api/tunnels/edit/", methods=['POST'])
def edit_tunnel_without_id_with_slash():
    return {"status": "state.tunnel.edit.invalid.data"}, 400

@app.route("/")
def idk():
    status = "state.tunnel.stopped"
    if mon.is_active():
      status = "state.tunnel.running"
    return {"status": status, "docs": "/docs/"}



@app.route('/docs/')
def serve_docs_main():
    return send_from_directory('docs', "index.html")

@app.route('/docs/<path:path>')
def serve_docs(path):
    return send_from_directory('docs', path)


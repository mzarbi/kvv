from flasgger import Swagger
from flask import Flask, Blueprint, request, jsonify
import Pyro4

# Create a Flask app and a blueprint
from web.api.routes import kv_store_api

app = Flask(__name__)
Swagger(app)
app.register_blueprint(kv_store_api, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
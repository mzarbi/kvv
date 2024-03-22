import Pyro4
from flask import Blueprint, request, jsonify

kv_store_api = Blueprint('kv-api', __name__)

host = "localhost"
port = 6666
uri = f"PYRO:key_value_store@{host}:{port}"


@kv_store_api.route('/update-config', methods=['POST'])
def update_config():
    """
        Update configuration
        ---
        tags:
          - Configuration
        parameters:
          - in: body
            name: body
            description: Configuration parameters
            required: true
            schema:
              type: object
              properties:
                backup_dir:
                  type: string
                  example: '/new/backup/dir'
                metrics_interval:
                  type: integer
                  example: 10
                status_ttl:
                  type: integer
                  example: 3600
                cleanup_frequency:
                  type: integer
                  example: 60
        responses:
          200:
            description: Configuration update was successful
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Configuration update sent to server.
          500:
            description: Error updating configuration
        """
    data = request.json
    with Pyro4.Proxy(uri) as proxy:
        proxy.update_configuration(**data)
    return jsonify({"message": "Configuration update sent to server."})


@kv_store_api.route('/show-config', methods=['GET'])
def show_config():
    """
        Retrieve server configuration
        ---
        tags:
          - Configuration
        responses:
          200:
            description: Server configuration retrieved successfully
            schema:
              type: object
              properties:
                backup_dir:
                  type: string
                  example: '/path/to/backup'
                metrics_interval:
                  type: integer
                  example: 60
                status_ttl:
                  type: integer
                  example: 3600
                cleanup_frequency:
                  type: integer
                  example: 120
        """
    with Pyro4.Proxy(uri) as proxy:
        config = proxy.get_configuration()
    return jsonify(config)


@kv_store_api.route('/shutdown', methods=['POST'])
def shutdown_task():
    """
        Shutdown a specific task or all tasks
        ---
        tags:
          - Task Management
        parameters:
          - name: task_name
            in: body
            required: false
            schema:
              type: object
              properties:
                task_name:
                  type: string
                  example: 'cleanup'
        responses:
          200:
            description: Task(s) shutdown successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: 'Shutdown signal sent to task: cleanup.'
        """
    task_name = request.json.get('task_name')
    with Pyro4.Proxy(uri) as proxy:
        if task_name:
            proxy.shutdown(task_name=task_name)
        else:
            proxy.shutdown()
    return jsonify({"message": f"Shutdown signal sent to task: {task_name if task_name else 'all tasks'}."})


@kv_store_api.route('/start-task', methods=['POST'])
def start_task():
    """
        Starts a specific task or all tasks
        ---
        tags:
          - Task Management
        parameters:
          - name: task_name
            in: body
            required: false
            schema:
              type: object
              properties:
                task_name:
                  type: string
                  example: 'metrics_collection'
        responses:
          200:
            description: Task(s) started successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: 'Start signal sent to task: metrics_collection.'
        """
    task_name = request.json.get('task_name')
    with Pyro4.Proxy(uri) as proxy:
        if task_name:
            proxy.start_tasks(task_name=task_name)
        else:
            proxy.start_tasks()
    return jsonify({"message": f"Start signal sent to task: {task_name if task_name else 'all tasks'}."})


@kv_store_api.route('/create-store', methods=['POST'])
def create_store():
    """
        Creates a new store
        ---
        tags:
          - Store Management
        parameters:
          - name: store_name
            in: body
            required: true
            schema:
              type: object
              properties:
                store_name:
                  type: string
                  example: 'my_new_store'
        responses:
          201:
            description: Store created successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: 'Store "my_new_store" created successfully.'
          400:
            description: Error in creating store
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Store "my_new_store" already exists or could not be created.'
        """
    store_name = request.json.get('store_name')
    with Pyro4.Proxy(uri) as proxy:
        result = proxy.create_store(store_name)
        if result:
            return jsonify({"message": f"Store '{store_name}' created successfully."}), 201
        else:
            return jsonify({"error": f"Store '{store_name}' already exists or could not be created."}), 400


@kv_store_api.route('/delete-store', methods=['DELETE'])
def delete_store():
    """
        Deletes an existing store
        ---
        tags:
          - Store Management
        parameters:
          - name: store_name
            in: query
            type: string
            required: true
            description: Name of the store to delete
        responses:
          200:
            description: Store deleted successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: 'Store "my_store" deleted successfully.'
          404:
            description: Store not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Store "my_store" does not exist.'
        """
    store_name = request.args.get('store_name')
    with Pyro4.Proxy(uri) as proxy:
        result = proxy.delete_store(store_name)
        if result:
            return jsonify({"message": f"Store '{store_name}' deleted successfully."}), 200
        else:
            return jsonify({"error": f"Store '{store_name}' does not exist."}), 404


@kv_store_api.route('/list-stores', methods=['GET'])
def list_stores():
    """
        Lists all the stores
        ---
        tags:
          - Store Management
        responses:
          200:
            description: A list of all stores
            schema:
              type: object
              properties:
                stores:
                  type: array
                  items:
                    type: string
                  example: ["store1", "store2", "store3"]
        """
    with Pyro4.Proxy(uri) as proxy:
        stores = proxy.list_stores()
        return jsonify({"stores": stores}), 200


@kv_store_api.route('/add-internal-key', methods=['POST'])
def add_internal_key():
    """
        Adds a key to the internal store
        ---
        tags:
          - Key Management
        parameters:
          - name: key
            in: formData
            type: string
            required: true
            description: The key to add
          - name: value
            in: formData
            type: string
            required: true
            description: The value associated with the key
          - name: ttl
            in: formData
            type: integer
            required: false
            description: Time to live for the key
          - name: readonly
            in: formData
            type: boolean
            required: false
            default: false
            description: Marks the key as read-only
        responses:
          201:
            description: Key added successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Key 'exampleKey' added to the internal store.
          400:
            description: Error adding key
        """
    key = request.json.get('key')
    value = request.json.get('value')
    ttl = request.json.get('ttl', None)
    readonly = request.json.get('readonly', False)
    with Pyro4.Proxy(uri) as proxy:
        proxy.add_internal_key(key, value, ttl, readonly)
        return jsonify({"message": f"Key '{key}' added to the internal store."}), 201


@kv_store_api.route('/delete-internal-key/<key>', methods=['DELETE'])
def delete_internal_key(key):
    """
        Deletes a key from the internal store
        ---
        tags:
          - Key Management
        parameters:
          - name: key
            in: path
            type: string
            required: true
            description: The key to delete
        responses:
          200:
            description: Key deleted successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Key 'exampleKey' deleted from the internal store.
          404:
            description: Key not found
        """
    with Pyro4.Proxy(uri) as proxy:
        proxy.delete_internal_key(key)
        return jsonify({"message": f"Key '{key}' deleted from the internal store."}), 200


@kv_store_api.route('/edit-internal-key', methods=['PUT'])
def edit_internal_key():
    """
        Edits an existing key within the internal store
        ---
        tags:
          - Key Management
        parameters:
          - in: body
            name: body
            description: The key details to update
            required: true
            schema:
              type: object
              required:
                - key
              properties:
                key:
                  type: string
                  description: The key to edit
                value:
                  type: string
                  description: New value for the key
                ttl:
                  type: integer
                  description: New time to live for the key
                readonly:
                  type: boolean
                  description: Set the key as read-only
        responses:
          200:
            description: Key updated successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Key 'exampleKey' has been updated in the internal store.
          404:
            description: Key not found
        """
    key = request.json.get('key')
    value = request.json.get('value', None)
    ttl = request.json.get('ttl', None)
    readonly = request.json.get('readonly', None)
    with Pyro4.Proxy(uri) as proxy:
        proxy.edit_internal_key(key, value, ttl, readonly)
        return jsonify({"message": f"Key '{key}' has been updated in the internal store."}), 200


@kv_store_api.route('/get-internal-key/<key>', methods=['GET'])
def get_internal_key(key):
    """
        Retrieves the value of a specific key from the internal store
        ---
        tags:
          - Key Management
        parameters:
          - in: path
            name: key
            required: true
            type: string
            description: The key to retrieve
        responses:
          200:
            description: Key value retrieved successfully
            schema:
              type: object
              properties:
                key:
                  type: string
                  example: exampleKey
                value:
                  type: string
                  example: exampleValue
          404:
            description: Key not found
        """
    with Pyro4.Proxy(uri) as proxy:
        value = proxy.get_internal_key(key)
        return jsonify({"key": key, "value": value}), 200


@kv_store_api.route('/get-all-internal-keys', methods=['GET'])
def get_all_internal_keys():
    """
        Retrieves all keys and their values from the internal store
        ---
        tags:
          - Key Management
        responses:
          200:
            description: All keys and their values retrieved successfully
            schema:
              type: object
              properties:
                keys:
                  type: object
                  example: { "exampleKey1": "exampleValue1", "exampleKey2": "exampleValue2" }
        """
    with Pyro4.Proxy(uri) as proxy:
        keys_values = proxy.get_all_internal_keys()
        return jsonify({"keys": keys_values}), 200


@kv_store_api.route('/list-pipelines', methods=['GET'])
def list_pipelines():
    """
        Lists all pipelines in the store
        ---
        tags:
          - Pipeline Management
        responses:
          200:
            description: A list of all pipelines
            schema:
              type: object
              properties:
                pipelines:
                  type: array
                  items:
                    type: string
                  example: ["pipeline1", "pipeline2", "pipeline3"]
        """
    with Pyro4.Proxy(uri) as proxy:
        pipelines = proxy.list_pipelines()
        return jsonify({"pipelines": pipelines}), 200


@kv_store_api.route('/pipelines/<pipeline_id>', methods=['GET'])
def get_pipeline(pipeline_id):
    """
    Fetch a specific pipeline by its ID
    ---
    tags:
      - Pipeline Management
    parameters:
      - name: pipeline_id
        in: path
        type: string
        required: true
        description: The ID of the pipeline to retrieve
    responses:
      200:
        description: A specific pipeline retrieved successfully
        schema:
          type: object
          properties:
            pipeline:
              type: object
              example: { "id": "pipeline1", "creator": "creator_name", "description": "A sample pipeline", "metadata": {}, "cfg": {}, "stages": [], "status": "Not Started", "errors": [] }
      404:
        description: Pipeline not found
    """
    with Pyro4.Proxy(uri) as proxy:
        pipeline = proxy.get_pipeline(pipeline_id)
        return jsonify({"pipeline": pipeline}), 200


@kv_store_api.route('/add-update-path', methods=['POST'])
def add_update_path():
    """
        Adds or updates a path for a given label, environment, and system.
        ---
        tags:
          - Paths Management
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - label
                - env
                - system
                - path
              properties:
                label:
                  type: string
                  description: The label of the path.
                env:
                  type: string
                  description: The environment of the path (e.g., dev, prod).
                system:
                  type: string
                  description: The system type (e.g., posix, nt).
                path:
                  type: string
                  description: The actual path.
        responses:
          201:
            description: Path updated successfully.
          400:
            description: Invalid request parameters.
        """
    label = request.json.get('label')
    env = request.json.get('env')
    system = request.json.get('system')
    path = request.json.get('path')
    with Pyro4.Proxy(uri) as proxy:
        proxy.add_or_update_path(label, env, system, path)
        return jsonify({"message": f"Path for '{label}' in {env}/{system} updated to: {path}"}), 201


@kv_store_api.route('/get-path/<label>/<env>/<system>', methods=['GET'])
def get_path(label, env, system):
    """
        Retrieves a specific path for a given label, environment, and system.
        ---
        tags:
          - Paths Management
        parameters:
          - name: label
            in: path
            type: string
            required: true
            description: The label of the path.
          - name: env
            in: path
            type: string
            required: true
            description: The environment of the path (e.g., dev, prod).
          - name: system
            in: path
            type: string
            required: true
            description: The system type (e.g., posix, nt).
        responses:
          200:
            description: The requested path.
            schema:
              type: object
              properties:
                path:
                  type: string
                  description: The actual path.
          404:
            description: Path not found.
        """
    with Pyro4.Proxy(uri) as proxy:
        path = proxy.get_path(label, env, system)
        if path:
            return jsonify({"path": path}), 200
        else:
            return jsonify({"error": f"No path found for '{label}' in {env}/{system}"}), 404


@kv_store_api.route('/update-paths-object', methods=['PUT'])
def update_paths_object():
    """
        Updates the entire paths object for a given label.
        ---
        tags:
          - Paths Management
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - label
                - new_paths
              properties:
                label:
                  type: string
                  description: The label of the path.
                new_paths:
                  type: object
                  description: The new paths object to update.
        responses:
          200:
            description: Paths object updated successfully.
          400:
            description: Invalid request parameters.
        """
    label = request.json.get('label')
    new_paths = request.json.get('new_paths')
    with Pyro4.Proxy(uri) as proxy:
        proxy.update_paths_object(label, new_paths)
        return jsonify({"message": f"Paths object for '{label}' updated."}), 200


@kv_store_api.route('/get-all-paths', methods=['GET'])
def get_all_paths():
    """
    Retrieves all paths stored in the server.
    ---
    tags:
      - Paths Management
    responses:
      200:
        description: Successfully retrieved all paths.
        schema:
          type: object
          properties:
            paths:
              type: object
              description: An object containing all paths.
    """
    with Pyro4.Proxy(uri) as proxy:
        paths = proxy.get_all_paths()
        return jsonify({"paths": paths}), 200


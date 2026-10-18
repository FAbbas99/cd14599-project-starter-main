from flask import Flask, request, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException
from backend.order_tracker import OrderTracker
from backend.in_memory_storage import InMemoryStorage

app = Flask(__name__, static_folder='../frontend')
in_memory_storage = InMemoryStorage()
order_tracker = OrderTracker(in_memory_storage)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

def error_response(message, code):
    return jsonify({"error": message}), code

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    # Unknown URL (404), wrong method (405), etc. -> same JSON shape as every other error
    return error_response(e.description, e.code)

@app.errorhandler(500)
def handle_server_error(_error):
    return error_response("Internal server error.", 500)

@app.route('/api/orders', methods=['POST'])
def add_order_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("Request body must be JSON.", 400)

    required = ["order_id", "item_name", "quantity", "customer_id"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}.", 400)

    try:
        order = order_tracker.add_order(
            data["order_id"],
            data["item_name"],
            data["quantity"],
            data["customer_id"],
            data.get("status", "pending"),
        )
    except ValueError as e:
        # Duplicate ID -> 409 Conflict
        return error_response(str(e), 409)
    return jsonify(order), 201

@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    order = order_tracker.get_order_by_id(order_id)
    if order is None:
        return error_response(f"Order with ID '{order_id}' not found.", 404)
    return jsonify(order), 200

@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status_api(order_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("new_status"):
        return error_response("Missing required field: new_status.", 400)

    if order_tracker.get_order_by_id(order_id) is None:
        return error_response(f"Order with ID '{order_id}' not found.", 404)

    try:
        order = order_tracker.update_order_status(order_id, data["new_status"])
    except ValueError as e:
        # Order exists, so the only failure left is an invalid status
        return error_response(str(e), 400)
    return jsonify(order), 200

@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")
    try:
        if customer_id:
            # status (if given) is applied together with customer_id
            orders = order_tracker.list_orders_by_customer(customer_id, status or None)
        elif status:
            orders = order_tracker.list_orders_by_status(status)
        else:
            orders = order_tracker.list_all_orders()
    except ValueError as e:
        return error_response(str(e), 400)
    return jsonify(orders), 200

@app.route('/api/orders/<string:order_id>', methods=['DELETE'])
def delete_order_api(order_id):
    if order_tracker.get_order_by_id(order_id) is None:
        return error_response(f"Order with ID '{order_id}' not found.", 404)
    order_tracker.delete_order(order_id)
    return "", 204

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

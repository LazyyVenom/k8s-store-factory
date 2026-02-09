from flask import Flask, jsonify, request
from flask_cors import CORS
from store_manager import StoreManager

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

store_manager = StoreManager()

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "healthy"})

@app.route('/api/stores', methods=['GET'])
def list_stores():
    """List all stores"""
    try:
        stores = store_manager.list_stores()
        return jsonify({"stores": stores})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stores', methods=['POST'])
def create_store():
    """Create a new store"""
    try:
        data = request.get_json() or {}
        sample_products = data.get('sample_products', "Sample Product 1|10.00|This is a sample product\nSample Product 2|20.00|Another sample product")
        store_url_suffix = data.get('store_url', None)
        admin_password = data.get('admin_password', None)
        
        result = store_manager.create_store(
            sample_products=sample_products, 
            store_url_suffix=store_url_suffix,
            admin_password=admin_password
        )
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stores/<store_id>', methods=['DELETE'])
def delete_store(store_id):
    """Delete a store"""
    try:
        result = store_manager.delete_store(store_id)
        if "error" in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000, debug=True)
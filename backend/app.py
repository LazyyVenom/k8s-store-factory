from flask import Flask, jsonify, request
from flask_cors import CORS
from store_manager import StoreManager

import database
from models import db, bcrypt, User
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store_factory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key-change-this-in-production'

CORS(app)  # Allow frontend to call this API

db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

database.init_db(app)

store_manager = StoreManager()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token, user_id=user.id, username=user.username), 200
        
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "healthy"})

@app.route('/api/users/me', methods=['GET'])
@jwt_required()
def get_current_user_quota():
    """Get usage quota for current user"""
    try:
        user_id = int(get_jwt_identity())
        user = database.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        usage = database.get_user_usage(user_id)
        return jsonify({
            "username": user['username'],
            "max_stores": user['max_stores'],
            "max_storage": user['max_storage_gi'],
            "current_stores": usage['store_count'] or 0,
            "current_storage": usage['total_storage'] or 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stores', methods=['GET'])
@jwt_required()
def list_stores():
    """List all stores for the authenticated user"""
    try:
        current_user_id = int(get_jwt_identity())
        stores = store_manager.list_stores(user_id=current_user_id)
        return jsonify({"stores": stores})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stores', methods=['POST'])
@jwt_required()
def create_store():
    """Create a new store"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        sample_products = data.get('sample_products', "Sample Product 1|10.00|This is a sample product\nSample Product 2|20.00|Another sample product")
        store_url_suffix = data.get('store_url', None)
        admin_password = data.get('admin_password', None)
        storage_size = int(data.get('storage_size_gi', 2))
        
        result = store_manager.create_store(
            user_id=current_user_id,
            sample_products=sample_products, 
            store_url_suffix=store_url_suffix,
            admin_password=admin_password,
            storage_size_gi=storage_size
        )
        if "error" in result:
            return jsonify(result), 500 # Should use 400 for logic errors but following existing pattern
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stores/<store_id>', methods=['DELETE'])
@jwt_required()
def delete_store(store_id):
    """Delete a store"""
    try:
        current_user_id = int(get_jwt_identity())
        result = store_manager.delete_store(store_id, user_id=current_user_id)
        if "error" in result:
            status_code = 403 if "Unauthorized" in result.get("error", "") else 404
            return jsonify(result), status_code
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000, debug=True)
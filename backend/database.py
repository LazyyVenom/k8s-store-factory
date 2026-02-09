from models import db, User, Store
from sqlalchemy import func

def init_db(app):
    with app.app_context():
        db.create_all()
        
        # Create default users if none exist
        if User.query.count() == 0:
            print("Initializing default users...")
            admin = User(username='admin', max_stores=10, max_storage_gi=50)
            admin.set_password('admin123')
            
            demo = User(username='demo_user', max_stores=2, max_storage_gi=5)
            demo.set_password('demo123')
            
            db.session.add_all([admin, demo])
            db.session.commit()

def get_user(user_id):
    user = db.session.get(User, user_id)
    if user:
        return user.to_dict()
    return None

def get_user_usage(user_id):
    result = db.session.query(
        func.count(Store.id).label('store_count'),
        func.sum(Store.storage_size_gi).label('total_storage')
    ).filter(Store.user_id == user_id).first()
    
    return {
        'store_count': result.store_count or 0,
        'total_storage': result.total_storage or 0
    }

def register_store(store_id, user_id, storage_size_gi, name=""):
    store = Store(
        id=store_id,
        user_id=user_id,
        storage_size_gi=storage_size_gi,
        name=name
    )
    db.session.add(store)
    db.session.commit()

def deregister_store(store_id):
    store = db.session.get(Store, store_id)
    if store:
        db.session.delete(store)
        db.session.commit()

def get_all_users():
    users = User.query.all()
    return [u.to_dict() for u in users]

def get_all_stores_with_users():
    stores = Store.query.options(db.joinedload(Store.user)).all()
    result = {}
    for s in stores:
        s_dict = s.to_dict()
        if s.user:
            s_dict['username'] = s.user.username
        result[s.id] = s_dict
    return result

# For legacy compatibility, though direct mapping is preferred
def get_db_connection():
    raise NotImplementedError("Use SQLAlchemy models instead of raw connection")

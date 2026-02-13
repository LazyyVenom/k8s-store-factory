from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from flask_bcrypt import Bcrypt

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    max_stores = db.Column(db.Integer, default=3)
    max_storage_gi = db.Column(db.Integer, default=10)
    
    # Relationship
    stores = db.relationship('Store', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'max_stores': self.max_stores,
            'max_storage_gi': self.max_storage_gi
        }

class Store(db.Model):
    __tablename__ = 'stores'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String)
    storage_size_gi = db.Column(db.Integer, default=2)
    status = db.Column(db.String, default='initialized')  # initialized, provisioning, ready, failed, deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', back_populates='stores')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'storage_size_gi': self.storage_size_gi,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

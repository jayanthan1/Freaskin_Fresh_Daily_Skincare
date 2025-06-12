# Freskin Flask Backend Application
# app.py

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets
import uuid
from functools import wraps
import jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///freskin.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
CORS(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    
    # Relationships
    subscription = db.relationship('Subscription', backref='user')
    skin_profile = db.relationship('SkinProfile', backref='user', uselist=False)
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            'subscription': self.subscription.to_dict() if self.subscription else None
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_type = db.Column(db.String(50), nullable=False)  # basic, premium, luxury
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    features = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_type': self.plan_type,
            'price': self.price,
            'duration_days': self.duration_days,
            'features': self.features.split(',') if self.features else [],
            'is_active': self.is_active
        }

class SkinProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skin_type = db.Column(db.String(50), nullable=False)  # oily, dry, combination, sensitive
    skin_concerns = db.Column(db.String(200), nullable=True)  # acne, aging, pigmentation, etc.
    allergies = db.Column(db.String(200), nullable=True)
    preferred_ingredients = db.Column(db.String(200), nullable=True)
    skin_tone = db.Column(db.String(50), nullable=True)
    current_routine = db.Column(db.String(100), nullable=True)  # daily, weekly, rarely, never
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'skin_type': self.skin_type,
            'skin_concerns': self.skin_concerns.split(',') if self.skin_concerns else [],
            'allergies': self.allergies.split(',') if self.allergies else [],
            'preferred_ingredients': self.preferred_ingredients.split(',') if self.preferred_ingredients else [],
            'skin_tone': self.skin_tone,
            'current_routine': self.current_routine,
            'updated_at': self.updated_at.isoformat()
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # cleanser, toner, mask, etc.
    ingredients = db.Column(db.Text, nullable=False)
    skin_types = db.Column(db.String(200), nullable=False)  # suitable skin types
    benefits = db.Column(db.Text, nullable=True)
    usage_instructions = db.Column(db.Text, nullable=True)
    shelf_life_hours = db.Column(db.Integer, default=24)  # freshness duration
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'ingredients': self.ingredients.split(',') if self.ingredients else [],
            'skin_types': self.skin_types.split(',') if self.skin_types else [],
            'benefits': self.benefits.split(',') if self.benefits else [],
            'usage_instructions': self.usage_instructions,
            'shelf_life_hours': self.shelf_life_hours,
            'price': self.price
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    delivery_time = db.Column(db.String(20), nullable=False)  # morning, evening, night
    status = db.Column(db.String(50), default='preparing')  # preparing, dispatched, delivered
    total_amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    special_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'delivery_date': self.delivery_date.isoformat(),
            'delivery_time': self.delivery_time,
            'status': self.status,
            'total_amount': self.total_amount,
            'delivery_address': self.delivery_address,
            'special_instructions': self.special_instructions,
            'items': [item.to_dict() for item in self.order_items],
            'created_at': self.created_at.isoformat()
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='order_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product': self.product.to_dict(),
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.quantity * self.unit_price
        }

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Routes

@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        # Send welcome email
        send_welcome_email(user.email, user.name)
        
        return jsonify({
            'message': 'Registration successful',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skin-quiz', methods=['POST'])
@token_required
def skin_quiz(current_user):
    """Process skin analysis quiz"""
    try:
        data = request.get_json()
        
        # Create or update skin profile
        skin_profile = SkinProfile.query.filter_by(user_id=current_user.id).first()
        
        if not skin_profile:
            skin_profile = SkinProfile(user_id=current_user.id)
        
        skin_profile.skin_type = data.get('skin_type')
        skin_profile.skin_concerns = ','.join(data.get('concerns', []))
        skin_profile.current_routine = data.get('routine_frequency')
        skin_profile.allergies = ','.join(data.get('allergies', []))
        skin_profile.preferred_ingredients = ','.join(data.get('preferred_ingredients', []))
        
        db.session.add(skin_profile)
        db.session.commit()
        
        # Generate personalized recommendations
        recommendations = generate_product_recommendations(skin_profile)
        
        return jsonify({
            'message': 'Skin profile updated successfully',
            'recommendations': recommendations,
            'skin_profile': skin_profile.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all available products"""
    try:
        products = Product.query.filter_by(is_active=True).all()
        
        # Filter by skin type if provided
        skin_type = request.args.get('skin_type')
        if skin_type:
            products = [p for p in products if skin_type in p.skin_types]
        
        return jsonify({
            'products': [product.to_dict() for product in products]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """Get available subscription plans"""
    try:
        subscriptions = Subscription.query.filter_by(is_active=True).all()
        
        return jsonify({
            'subscriptions': [sub.to_dict() for sub in subscriptions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscribe', methods=['POST'])
@token_required
def subscribe(current_user):
    """Subscribe user to a plan"""
    try:
        data = request.get_json()
        subscription_id = data.get('subscription_id')
        
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Update user subscription
        current_user.subscription_id = subscription_id
        db.session.commit()
        
        # Create initial orders for the subscription period
        create_subscription_orders(current_user)
        
        # Send confirmation email
        send_subscription_confirmation(current_user.email, current_user.name, subscription.plan_type)
        
        return jsonify({
            'message': 'Subscription successful',
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    """Get user's orders"""
    try:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.delivery_date.desc()).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/today', methods=['GET'])
@token_required
def get_today_orders(current_user):
    """Get today's orders"""
    try:
        today = datetime.now().date()
        orders = Order.query.filter_by(
            user_id=current_user.id,
            delivery_date=today
        ).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get user profile"""
    try:
        profile_data = current_user.to_dict()
        profile_data['skin_profile'] = current_user.skin_profile.to_dict() if current_user.skin_profile else None
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Update user fields
        if 'name' in data:
            current_user.name = data['name']
        if 'phone' in data:
            current_user.phone = data['phone']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper Functions

def generate_product_recommendations(skin_profile):
    """Generate personalized product recommendations based on skin profile"""
    recommendations = {
        'morning_routine': [],
        'evening_routine': [],
        'weekly_treatments': [],
        'recommended_plan': 'premium'
    }
    
    # Get products suitable for user's skin type
    suitable_products = Product.query.filter(
        Product.skin_types.contains(skin_profile.skin_type),
        Product.is_active == True
    ).all()
    
    # Categorize products by routine
    for product in suitable_products:
        if product.category in ['cleanser', 'toner', 'moisturizer']:
            recommendations['morning_routine'].append(product.to_dict())
        elif product.category in ['serum', 'night_cream', 'oil']:
            recommendations['evening_routine'].append(product.to_dict())
        elif product.category in ['mask', 'scrub', 'treatment']:
            recommendations['weekly_treatments'].append(product.to_dict())
    
    # Limit recommendations to avoid overwhelming user
    for key in recommendations:
        if isinstance(recommendations[key], list):
            recommendations[key] = recommendations[key][:3]
    
    return recommendations

def create_subscription_orders(user):
    """Create initial orders for a new subscription"""
    if not user.subscription:
        return
    
    start_date = datetime.now().date()
    
    # Create orders for the next 7 days
    for i in range(7):
        delivery_date = start_date + timedelta(days=i)
        
        # Create morning order
        morning_order = Order(
            user_id=user.id,
            order_number=f"FR{uuid.uuid4().hex[:8].upper()}",
            delivery_date=delivery_date,
            delivery_time="morning",
            status="preparing",
            total_amount=0.0,
            delivery_address="",
            special_instructions=""
        )
        db.session.add(morning_order)

        # Create evening order
        evening_order = Order(
            user_id=user.id,
            order_number=f"FR{uuid.uuid4().hex[:8].upper()}",
            delivery_date=delivery_date,
            delivery_time="evening",
            status="preparing",
            total_amount=0.0,
            delivery_address="",
            special_instructions=""
        )
        db.session.add(evening_order)
        
        # Create weekly treatment order
        weekly_treatment_order = Order(
            user_id=user.id,
            order_number=f"FR{uuid.uuid4().hex[:8].upper()}",
            delivery_date=delivery_date,
            delivery_time="weekly_treatment",
            status="preparing",
            total_amount=0.0,
            delivery_address="",
            special_instructions=""
        )
        db.session.add(weekly_treatment_order)
    
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
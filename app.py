# Additional features to add to your existing Freskin Flask app
# Add these to your existing app.py file

# Add these imports to your existing imports section
from datetime import date
import random
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Add these new models to your existing models section

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    weather_condition = db.Column(db.String(50), nullable=False)  # sunny, rainy, humid, dry
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'weather_condition': self.weather_condition,
            'recorded_at': self.recorded_at.isoformat()
        }

class CustomizationPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delivery_time_preference = db.Column(db.String(20), default='morning')  # morning, evening, both
    frequency = db.Column(db.String(20), default='daily')  # daily, alternate, weekly
    packaging_preference = db.Column(db.String(50), default='glass')  # glass, compostable, bamboo
    special_dietary_restrictions = db.Column(db.String(200), nullable=True)
    weather_adaptation = db.Column(db.Boolean, default=True)
    stress_level_consideration = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='customization_prefs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'delivery_time_preference': self.delivery_time_preference,
            'frequency': self.frequency,
            'packaging_preference': self.packaging_preference,
            'special_dietary_restrictions': self.special_dietary_restrictions,
            'weather_adaptation': self.weather_adaptation,
            'stress_level_consideration': self.stress_level_consideration
        }

class DeliveryZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    zone_name = db.Column(db.String(100), nullable=False)
    pincode_range = db.Column(db.String(200), nullable=False)  # comma separated pincodes
    delivery_slots = db.Column(db.String(200), nullable=False)  # morning:6-9,evening:5-8
    preparation_time_hours = db.Column(db.Integer, default=2)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'zone_name': self.zone_name,
            'pincode_range': self.pincode_range.split(','),
            'delivery_slots': dict(slot.split(':') for slot in self.delivery_slots.split(',') if ':' in slot),
            'preparation_time_hours': self.preparation_time_hours
        }

class ProductBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    batch_number = db.Column(db.String(50), unique=True, nullable=False)
    preparation_date = db.Column(db.DateTime, nullable=False)
    expiry_datetime = db.Column(db.DateTime, nullable=False)
    quantity_prepared = db.Column(db.Integer, nullable=False)
    preparation_location = db.Column(db.String(100), nullable=False)
    quality_score = db.Column(db.Float, default=5.0)  # out of 5
    ingredients_source = db.Column(db.Text, nullable=True)  # local farm details
    
    # Relationship
    product = db.relationship('Product', backref='batches')
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_number': self.batch_number,
            'preparation_date': self.preparation_date.isoformat(),
            'expiry_datetime': self.expiry_datetime.isoformat(),
            'quantity_prepared': self.quantity_prepared,
            'preparation_location': self.preparation_location,
            'quality_score': self.quality_score,
            'ingredients_source': self.ingredients_source,
            'freshness_hours_left': self.get_freshness_hours_left()
        }
    
    def get_freshness_hours_left(self):
        if self.expiry_datetime > datetime.utcnow():
            return int((self.expiry_datetime - datetime.utcnow()).total_seconds() / 3600)
        return 0

class UserFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    skin_reaction = db.Column(db.String(50), nullable=True)  # positive, neutral, negative
    effectiveness = db.Column(db.Integer, nullable=True)  # 1-5
    texture_preference = db.Column(db.String(50), nullable=True)
    fragrance_preference = db.Column(db.String(50), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    would_reorder = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='feedbacks')
    order = db.relationship('Order', backref='feedbacks')
    product = db.relationship('Product', backref='feedbacks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'skin_reaction': self.skin_reaction,
            'effectiveness': self.effectiveness,
            'texture_preference': self.texture_preference,
            'fragrance_preference': self.fragrance_preference,
            'comments': self.comments,
            'would_reorder': self.would_reorder,
            'created_at': self.created_at.isoformat()
        }

# Add these new routes to your existing routes section

@app.route('/api/weather-adaptive-products', methods=['GET'])
@token_required
def get_weather_adaptive_products(current_user):
    """Get products adapted to current weather conditions"""
    try:
        city = request.args.get('city', 'Mumbai')  # Default city
        
        # Get current weather (you can integrate with weather API)
        weather = get_current_weather(city)
        
        # Get products based on weather
        adaptive_products = get_products_for_weather(weather, current_user.skin_profile)
        
        return jsonify({
            'weather': weather,
            'recommended_products': adaptive_products,
            'adaptation_message': get_weather_adaptation_message(weather)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customization-preferences', methods=['POST'])
@token_required
def set_customization_preferences(current_user):
    """Set user's delivery and product customization preferences"""
    try:
        data = request.get_json()
        
        # Check if preferences already exist
        prefs = CustomizationPreferences.query.filter_by(user_id=current_user.id).first()
        
        if not prefs:
            prefs = CustomizationPreferences(user_id=current_user.id)
        
        # Update preferences
        prefs.delivery_time_preference = data.get('delivery_time_preference', 'morning')
        prefs.frequency = data.get('frequency', 'daily')
        prefs.packaging_preference = data.get('packaging_preference', 'glass')
        prefs.special_dietary_restrictions = data.get('special_dietary_restrictions', '')
        prefs.weather_adaptation = data.get('weather_adaptation', True)
        prefs.stress_level_consideration = data.get('stress_level_consideration', False)
        
        db.session.add(prefs)
        db.session.commit()
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': prefs.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delivery-zones', methods=['GET'])
def get_delivery_zones():
    """Get available delivery zones"""
    try:
        zones = DeliveryZone.query.filter_by(is_active=True).all()
        
        return jsonify({
            'delivery_zones': [zone.to_dict() for zone in zones],
            'coverage_message': 'Currently serving select metro areas with plans to expand soon!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-delivery-availability', methods=['POST'])
def check_delivery_availability():
    """Check if delivery is available for a specific pincode"""
    try:
        data = request.get_json()
        pincode = data.get('pincode')
        
        if not pincode:
            return jsonify({'error': 'Pincode is required'}), 400
        
        # Check if pincode is in any delivery zone
        zones = DeliveryZone.query.filter_by(is_active=True).all()
        available_zone = None
        
        for zone in zones:
            if pincode in zone.pincode_range.split(','):
                available_zone = zone
                break
        
        if available_zone:
            return jsonify({
                'available': True,
                'zone': available_zone.to_dict(),
                'message': f'Great! We deliver to your area in {available_zone.zone_name}'
            }), 200
        else:
            return jsonify({
                'available': False,
                'message': 'Sorry, we don\'t deliver to your area yet. We\'re expanding soon!',
                'waitlist_option': True
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fresh-batches', methods=['GET'])
@token_required
def get_fresh_batches(current_user):
    """Get information about fresh product batches"""
    try:
        # Get today's fresh batches
        today = datetime.now().date()
        fresh_batches = ProductBatch.query.filter(
            db.func.date(ProductBatch.preparation_date) == today,
            ProductBatch.expiry_datetime > datetime.utcnow()
        ).all()
        
        return jsonify({
            'fresh_batches': [batch.to_dict() for batch in fresh_batches],
            'total_fresh_products': len(fresh_batches),
            'freshness_guarantee': 'All products are made fresh daily and delivered within 4 hours of preparation'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personalized-routine', methods=['GET'])
@token_required
def get_personalized_routine(current_user):
    """Generate a complete personalized skincare routine"""
    try:
        if not current_user.skin_profile:
            return jsonify({'error': 'Please complete your skin quiz first'}), 400
        
        # Get user's preferences
        prefs = CustomizationPreferences.query.filter_by(user_id=current_user.id).first()
        
        # Generate comprehensive routine
        routine = generate_comprehensive_routine(current_user.skin_profile, prefs)
        
        return jsonify({
            'personalized_routine': routine,
            'routine_duration': '4-6 weeks for visible results',
            'next_review_date': (datetime.now() + timedelta(weeks=4)).strftime('%Y-%m-%d')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
@token_required
def submit_feedback(current_user):
    """Submit feedback for a product/order"""
    try:
        data = request.get_json()
        
        feedback = UserFeedback(
            user_id=current_user.id,
            order_id=data.get('order_id'),
            product_id=data.get('product_id'),
            rating=data.get('rating'),
            skin_reaction=data.get('skin_reaction'),
            effectiveness=data.get('effectiveness'),
            texture_preference=data.get('texture_preference'),
            fragrance_preference=data.get('fragrance_preference'),
            comments=data.get('comments', ''),
            would_reorder=data.get('would_reorder', True)
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        # Update future recommendations based on feedback
        update_recommendations_based_on_feedback(current_user, feedback)
        
        return jsonify({
            'message': 'Thank you for your feedback!',
            'points_earned': 10,  # Reward system
            'feedback_id': feedback.id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sustainability-impact', methods=['GET'])
@token_required
def get_sustainability_impact(current_user):
    """Get user's environmental impact through Freskin"""
    try:
        # Calculate sustainability metrics
        total_orders = Order.query.filter_by(user_id=current_user.id).count()
        
        sustainability_metrics = {
            'plastic_saved_grams': total_orders * 15,  # Avg 15g per traditional package
            'chemical_preservatives_avoided': total_orders * 3,  # Avg 3 preservatives per product
            'local_sourcing_percentage': 85,
            'carbon_footprint_reduction': total_orders * 0.2,  # kg CO2 saved
            'biodegradable_packaging_used': total_orders,
            'water_conservation_liters': total_orders * 2.5,
            'supporting_local_farmers': True
        }
        
        return jsonify({
            'sustainability_impact': sustainability_metrics,
            'eco_badge_level': calculate_eco_badge_level(total_orders),
            'next_milestone': get_next_eco_milestone(total_orders)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ingredient-transparency', methods=['GET'])
def get_ingredient_transparency():
    """Get detailed information about ingredients and their sources"""
    try:
        product_id = request.args.get('product_id')
        
        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            # Get ingredient details
            ingredient_details = get_detailed_ingredient_info(product)
            
            return jsonify({
                'product': product.to_dict(),
                'ingredient_transparency': ingredient_details,
                'sourcing_info': {
                    'local_farms': get_local_farm_info(),
                    'organic_certification': True,
                    'fair_trade': True,
                    'seasonal_availability': get_seasonal_ingredient_info()
                }
            }), 200
        else:
            # Return general ingredient information
            return jsonify({
                'common_ingredients': get_common_ingredient_benefits(),
                'avoided_chemicals': get_avoided_chemicals_list(),
                'sourcing_philosophy': 'Fresh, Local, Organic, Sustainable'
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions to add to your existing helper functions

def get_current_weather(city):
    """Get current weather data (integrate with weather API)"""
    # This is a mock function - integrate with actual weather API
    weather_conditions = ['sunny', 'humid', 'rainy', 'dry', 'windy']
    return {
        'city': city,
        'temperature': random.randint(20, 35),
        'humidity': random.randint(40, 80),
        'condition': random.choice(weather_conditions)
    }

def get_products_for_weather(weather, skin_profile):
    """Get products suitable for current weather conditions"""
    weather_product_mapping = {
        'humid': ['hydrating_gel', 'light_moisturizer', 'clay_mask'],
        'dry': ['rich_moisturizer', 'hydrating_serum', 'nourishing_oil'],
        'sunny': ['vitamin_c_serum', 'sunscreen', 'cooling_gel'],
        'rainy': ['gentle_cleanser', 'hydrating_toner', 'barrier_cream'],
        'windy': ['protective_balm', 'rich_moisturizer', 'soothing_serum']
    }
    
    condition = weather.get('condition', 'sunny')
    suitable_categories = weather_product_mapping.get(condition, ['moisturizer'])
    
    # Get products from these categories
    products = Product.query.filter(
        Product.category.in_(suitable_categories),
        Product.is_active == True
    ).limit(5).all()
    
    return [product.to_dict() for product in products]

def get_weather_adaptation_message(weather):
    """Get personalized message based on weather"""
    condition = weather.get('condition')
    humidity = weather.get('humidity', 50)
    
    messages = {
        'humid': f"It's humid today ({humidity}% humidity). We're sending lightweight, non-greasy formulations to keep your skin fresh!",
        'dry': "Dry weather detected. Your products today focus on deep hydration and barrier protection.",
        'sunny': "Sunny day ahead! Your routine includes antioxidant-rich products and natural sun protection.",
        'rainy': "Rainy weather calls for gentle, soothing products to maintain your skin's balance.",
        'windy': "Windy conditions today. We've selected protective and nourishing products for your skin barrier."
    }
    
    return messages.get(condition, "Perfect weather for your personalized skincare routine!")

def generate_comprehensive_routine(skin_profile, preferences):
    """Generate a detailed skincare routine"""
    routine = {
        'morning': {
            'steps': [
                {'step': 1, 'product': 'Gentle Cleanser', 'time': '30 seconds', 'instruction': 'Massage gently with damp hands'},
                {'step': 2, 'product': 'Hydrating Toner', 'time': '1 minute', 'instruction': 'Pat gently into skin'},
                {'step': 3, 'product': 'Vitamin C Serum', 'time': '2 minutes', 'instruction': 'Apply and let absorb'},
                {'step': 4, 'product': 'Daily Moisturizer', 'time': '1 minute', 'instruction': 'Apply in upward motions'}
            ],
            'total_time': '4-5 minutes'
        },
        'evening': {
            'steps': [
                {'step': 1, 'product': 'Deep Cleanser', 'time': '1 minute', 'instruction': 'Double cleanse if wearing makeup'},
                {'step': 2, 'product': 'Treatment Toner', 'time': '1 minute', 'instruction': 'Use cotton pad or pat with hands'},
                {'step': 3, 'product': 'Night Serum', 'time': '2 minutes', 'instruction': 'Focus on concern areas'},
                {'step': 4, 'product': 'Night Moisturizer', 'time': '1 minute', 'instruction': 'Apply generously'}
            ],
            'total_time': '5-6 minutes'
        },
        'weekly_treatments': [
            {'frequency': '2x per week', 'product': 'Exfoliating Mask', 'day': 'Wednesday, Sunday'},
            {'frequency': '1x per week', 'product': 'Deep Hydration Mask', 'day': 'Saturday'},
            {'frequency': '1x per week', 'product': 'Eye Treatment', 'day': 'Friday'}
        ],
        'skin_concerns_focus': skin_profile.skin_concerns.split(',') if skin_profile.skin_concerns else [],
        'expected_results_timeline': {
            '1 week': 'Improved skin texture and hydration',
            '2 weeks': 'Reduced irritation and better skin barrier',
            '4 weeks': 'Visible improvement in skin concerns',
            '8 weeks': 'Significant transformation and glow'
        }
    }
    
    return routine

def update_recommendations_based_on_feedback(user, feedback):
    """Update future recommendations based on user feedback"""
    # This function would implement ML logic to improve recommendations
    # For now, it's a placeholder for future implementation
    pass

def calculate_eco_badge_level(total_orders):
    """Calculate user's eco-consciousness badge level"""
    if total_orders >= 100:
        return 'Eco Champion'
    elif total_orders >= 50:
        return 'Green Guardian'
    elif total_orders >= 20:
        return 'Nature Lover'
    elif total_orders >= 5:
        return 'Eco Conscious'
    else:
        return 'Getting Started'

def get_next_eco_milestone(total_orders):
    """Get next environmental milestone"""
    milestones = [5, 20, 50, 100, 200]
    for milestone in milestones:
        if total_orders < milestone:
            return f"{milestone - total_orders} more orders to reach next eco milestone!"
    return "You've achieved all eco milestones! You're an environmental superhero!"

def get_detailed_ingredient_info(product):
    """Get detailed information about product ingredients"""
    # Mock detailed ingredient information
    ingredient_benefits = {
        'aloe_vera': {
            'benefits': ['Soothing', 'Anti-inflammatory', 'Hydrating'],
            'source': 'Organic farms in Rajasthan',
            'extraction_method': 'Cold-pressed',
            'purity': '99.5%'
        },
        'turmeric': {
            'benefits': ['Anti-bacterial', 'Brightening', 'Anti-aging'],
            'source': 'Kerala organic farms',
            'extraction_method': 'Traditional grinding',
            'purity': '98%'
        },
        'rose_water': {
            'benefits': ['Toning', 'Hydrating', 'Calming'],
            'source': 'Kashmir rose gardens',
            'extraction_method': 'Steam distillation',
            'purity': '100% natural'
        }
    }
    
    return ingredient_benefits

def get_local_farm_info():
    """Get information about partner farms"""
    return [
        {
            'name': 'Green Valley Organic Farm',
            'location': 'Pune, Maharashtra',
            'speciality': 'Aloe Vera, Neem, Tulsi',
            'certification': 'Organic India Certified'
        },
        {
            'name': 'Himalayan Herb Gardens',
            'location': 'Uttarakhand',
            'speciality': 'Rose, Lavender, Chamomile',
            'certification': 'NPOP Certified'
        }
    ]

def get_seasonal_ingredient_info():
    """Get seasonal availability of ingredients"""
    return {
        'summer': ['Cucumber', 'Mint', 'Aloe Vera', 'Rose'],
        'monsoon': ['Neem', 'Turmeric', 'Honey', 'Clay'],
        'winter': ['Almond Oil', 'Shea Butter', 'Oats', 'Milk'],
        'spring': ['Green Tea', 'Lemon', 'Papaya', 'Vitamin E']
    }

def get_common_ingredient_benefits():
    """Get benefits of commonly used natural ingredients"""
    return {
        'Natural Ingredients': {
            'Turmeric': 'Anti-inflammatory, brightening, antibacterial',
            'Aloe Vera': 'Soothing, hydrating, healing',
            'Rose Water': 'Toning, calming, pH balancing',
            'Honey': 'Moisturizing, antibacterial, gentle exfoliation',
            'Oats': 'Gentle cleansing, soothing, anti-inflammatory',
            'Cucumber': 'Cooling, hydrating, reduces puffiness'
        }
    }

def get_avoided_chemicals_list():
    """List of harmful chemicals that Freskin avoids"""
    return {
        'Parabens': 'Preservatives linked to hormone disruption',
        'Sulfates': 'Harsh cleansing agents that strip natural oils',
        'Silicones': 'Can clog pores and prevent skin breathing',
        'Artificial Fragrances': 'Can cause allergic reactions and sensitivity',
        'Formaldehyde': 'Carcinogenic preservative',
        'Phthalates': 'Endocrine disruptors found in fragrances'
    }

def send_welcome_email(email, name):
    """Send welcome email to new users"""
    try:
        subject = "Welcome to Freskin - Your Fresh Skincare Journey Begins! 🌿"
        body = f"""
        Dear {name},
        
        Welcome to the Freskin family! We're thrilled to have you on board for your fresh, chemical-free skincare journey.
        
        What makes Freskin special:
        ✨ 100% preservative-free products made fresh daily
        🌱 Natural ingredients sourced from local organic farms
        📦 Delivered fresh to your doorstep
        🎯 Personalized for your unique skin needs
        
        Next steps:
        1. Complete your skin analysis quiz
        2. Set your delivery preferences
        3. Choose your subscription plan
        4. Get ready for amazing skin!
        
        Questions? Reply to this email - we're here to help!
        
        Fresh regards,
        The Freskin Team
        """
        
        # Email sending logic here
        print(f"Welcome email sent to {email}")
        
    except Exception as e:
        print(f"Error sending welcome email: {e}")

def send_subscription_confirmation(email, name, plan_type):
    """Send subscription confirmation email"""
    try:
        subject = f"Freskin {plan_type.title()} Subscription Confirmed! 🎉"
        body = f"""
        Hi {name},
        
        Your Freskin {plan_type.title()} subscription is now active!
        
        What to expect:
        • Fresh products delivered daily
        • Weather-adapted formulations
        • Eco-friendly packaging
        • 24/7 customer support
        
        Your first delivery will arrive tomorrow morning between 6-9 AM.
        
        Track your orders and sustainability impact in the app!
        
        Fresh wishes,
        Team Freskin
        """
        
        # Email sending logic here
        print(f"Subscription confirmation sent to {email}")
        
    except Exception as e:
        print(f"Error sending subscription confirmation: {e}")

# Add these routes for the enhanced product catalog

@app.route('/api/products/categories', methods=['GET'])
def get_product_categories():
    """Get all product categories with their specialties"""
    try:
        categories = {
            'cleansers': {
                'name': 'Cleansers',
                'description': 'Fresh milk-based and fruit cleansers',
                'products': ['Raw Milk-Turmeric Cleanser', 'Honey-Oat Gentle Cleanser', 'Cucumber-Mint Face Wash']
            },
            'masks': {
                'name': 'Face Masks', 
                'description': 'Single-use fruit and herb masks',
                'products': ['Papaya-Honey Brightening Mask', 'Aloe-Cucumber Soothing Mask', 'Clay-Neem Purifying Mask']
            },
            'toners': {
                'name': 'Toners',
                'description': 'Natural floral and herbal toners',
                'products': ['Rose Water Toner', 'Mint-Cucumber Refresher', 'Green Tea-Aloe Toner']
            },
            'moisturizers': {
                'name': 'Moisturizers',
                'description': 'Hydrating gels and creams',
                'products': ['Aloe-Chia Hydrating Gel', 'Coconut-Shea Day Cream', 'Night Nourishing Oil Blend']
            },
            'treatments': {
                'name': 'Treatments',
                'description': 'Targeted eye and lip care',
                'products': ['Cucumber Eye Pads', 'Beetroot Lip Balm', 'Coffee-Coconut Under Eye Cream']
            },
            'scrubs': {
                'name': 'Exfoliators',
                'description': 'Gentle weekly scrubs',
                'products': ['Oatmeal-Yogurt Scrub', 'Sugar-Honey Body Polish', 'Rice-Milk Face Scrub']
            }
        }
        
        return jsonify({
            'categories': categories,
            'total_categories': len(categories)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database with sample data
def initialize_sample_data():
    """Initialize database with sample data"""
    try:
        # Create sample subscription plans
        if not Subscription.query.first():
            plans = [
                Subscription(
                    plan_type='basic',
                    price=999.0,
                    duration_days=30,
                    features='Daily cleanser,Weekly mask,Basic toner',
                    is_active=True
                ),
                Subscription(
                    plan_type='premium',
                    price=1999.0,
                    duration_days=30,
                    features='Full morning routine,Evening routine,Weekly treatments,Weather adaptation',
                    is_active=True
                ),
                Subscription(
                    plan_type='luxury',
                    price=2999.0,
                    duration_days=30,
                    features='Complete personalized routine,Twice daily delivery,Premium ingredients,Personal skin consultant,Express delivery',
                    is_active=True
                )
            ]
            
            for plan in plans:
                db.session.add(plan)
        
        # Create sample products based on your business idea
        if not Product.query.first():
            products = [
                # Face Masks
                Product(
                    name='Papaya-Honey Brightening Mask',
                    category='mask',
                    ingredients='Fresh papaya,Raw honey,Turmeric powder,Rose water',
                    skin_types='all,dull,pigmented',
                    benefits='Brightening,Exfoliation,Natural glow,Anti-aging',
                    usage_instructions='Apply thick layer, leave for 15 minutes, rinse with lukewarm water',
                    shelf_life_hours=12,
                    price=299.0,
                    is_active=True
                ),
                Product(
                    name='Cucumber-Aloe Cooling Mask',
                    category='mask',
                    ingredients='Fresh cucumber,Aloe vera gel,Mint extract,Glycerin',
                    skin_types='sensitive,oily,irritated',
                    benefits='Soothing,Cooling,Anti-inflammatory,Hydrating',
                    usage_instructions='Apply evenly, relax for 20 minutes, remove gently',
                    shelf_life_hours=24,
                    price=249.0,
                    is_active=True
                ),
                
                # Cleansers
                Product(
                    name='Raw Milk-Turmeric Cleanser',
                    category='cleanser',
                    ingredients='Raw milk,Turmeric,Chickpea flour,Rose water',
                    skin_types='dry,sensitive,mature',
                    benefits='Gentle cleansing,Moisturizing,Brightening,Anti-bacterial',
                    usage_instructions='Massage gently for 30 seconds, rinse with cool water',
                    shelf_life_hours=8,
                    price=199.0,
                    is_active=True
                ),
                Product(
                    name='Honey-Oat Gentle Cleanser',
                    category='cleanser',
                    ingredients='Raw honey,Ground oats,Coconut milk,Lavender oil',
                    skin_types='all,sensitive,acne-prone',
                    benefits='Deep cleansing,Exfoliation,Antibacterial,Calming',
                    usage_instructions='Work into lather with damp hands, massage and rinse',
                    shelf_life_hours=12,
                    price=179.0,
                    is_active=True
                ),
                
                # Toners
                Product(
                    name='Rose Water-Mint Toner',
                    category='toner',
                    ingredients='Pure rose water,Fresh mint,Witch hazel,Glycerin',
                    skin_types='all,oily,combination',
                    benefits='Toning,Refreshing,pH balancing,Pore minimizing',
                    usage_instructions='Apply with cotton pad or pat gently with hands',
                    shelf_life_hours=48,
                    price=149.0,
                    is_active=True
                ),
                Product(
                    name='Green Tea-Cucumber Toner',
                    category='toner',
                    ingredients='Fresh green tea,Cucumber juice,Aloe vera,Niacinamide',
                    skin_types='oily,acne-prone,dull',
                    benefits='Antioxidant,Oil control,Brightening,Anti-aging',
                    usage_instructions='Use twice daily after cleansing',
                    shelf_life_hours=36,
                    price=169.0,
                    is_active=True
                ),
                
                # Moisturizers
                Product(
                    name='Aloe-Chia Hydrating Gel',
                    category='moisturizer',
                    ingredients='Aloe vera gel,Chia seed extract,Hyaluronic acid,Vitamin E',
                    skin_types='oily,combination,sensitive',
                    benefits='Deep hydration,Light texture,Non-greasy,Cooling',
                    usage_instructions='Apply thin layer, perfect for humid weather',
                    shelf_life_hours=24,
                    price=229.0,
                    is_active=True
                ),
                Product(
                    name='Coconut-Shea Night Cream',
                    category='moisturizer',
                    ingredients='Virgin coconut oil,Shea butter,Jojoba oil,Vitamin C',
                    skin_types='dry,mature,normal',
                    benefits='Deep nourishment,Anti-aging,Repair,Softening',
                    usage_instructions='Apply generously before bed, massage gently',
                    shelf_life_hours=16,
                    price=279.0,
                    is_active=True
                ),
                
                # Eye & Lip Treatments
                Product(
                    name='Cucumber Eye Patches',
                    category='treatment',
                    ingredients='Fresh cucumber,Potato starch,Collagen,Caffeine',
                    skin_types='all,tired,puffy',
                    benefits='De-puffing,Dark circle reduction,Hydrating,Refreshing',
                    usage_instructions='Place under eyes for 15 minutes, use 3x per week',
                    shelf_life_hours=6,
                    price=199.0,
                    is_active=True
                ),
                Product(
                    name='Beetroot Lip Balm',
                    category='treatment',
                    ingredients='Fresh beetroot,Coconut oil,Beeswax,Vitamin E',
                    skin_types='all,dry,chapped',
                    benefits='Natural tint,Moisturizing,Healing,Plumping',
                    usage_instructions='Apply as needed throughout the day',
                    shelf_life_hours=72,
                    price=129.0,
                    is_active=True
                ),
                
                # Scrubs
                Product(
                    name='Oatmeal-Yogurt Gentle Scrub',
                    category='scrub',
                    ingredients='Ground oats,Fresh yogurt,Honey,Lemon juice',
                    skin_types='all,sensitive,dry',
                    benefits='Gentle exfoliation,Moisturizing,Brightening,Smoothing',
                    usage_instructions='Use 2x per week, massage gently in circular motions',
                    shelf_life_hours=8,
                    price=189.0,
                    is_active=True
                ),
                Product(
                    name='Coffee-Sugar Body Scrub',
                    category='scrub',
                    ingredients='Ground coffee,Brown sugar,Coconut oil,Vanilla extract',
                    skin_types='all,rough,cellulite',
                    benefits='Exfoliation,Circulation boost,Firming,Moisturizing',
                    usage_instructions='Use on damp skin in shower, scrub and rinse',
                    shelf_life_hours=12,
                    price=219.0,
                    is_active=True
                )
            ]
            
            for product in products:
                db.session.add(product)
        
        # Create sample delivery zones
        if not DeliveryZone.query.first():
            zones = [
                DeliveryZone(
                    city='Mumbai',
                    zone_name='South Mumbai',
                    pincode_range='400001,400002,400003,400004,400005,400020,400021',
                    delivery_slots='morning:6-9,evening:5-8,night:8-10',
                    preparation_time_hours=2,
                    is_active=True
                ),
                DeliveryZone(
                    city='Mumbai',
                    zone_name='Bandra-Andheri',
                    pincode_range='400050,400051,400052,400053,400058,400059,400061',
                    delivery_slots='morning:7-10,evening:6-9',
                    preparation_time_hours=3,
                    is_active=True
                ),
                DeliveryZone(
                    city='Delhi',
                    zone_name='Central Delhi',
                    pincode_range='110001,110002,110003,110011,110012,110055',
                    delivery_slots='morning:6-9,evening:5-8',
                    preparation_time_hours=2,
                    is_active=True
                ),
                DeliveryZone(
                    city='Bangalore',
                    zone_name='Koramangala-Indiranagar',
                    pincode_range='560034,560038,560047,560095,560008,560012',
                    delivery_slots='morning:7-10,evening:6-9',
                    preparation_time_hours=2,
                    is_active=True
                )
            ]
            
            for zone in zones:
                db.session.add(zone)
        
        db.session.commit()
        print("Sample data initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing sample data: {e}")

# Add more specialized routes for the business model

@app.route('/api/daily-fresh-report', methods=['GET'])
@token_required
def get_daily_fresh_report(current_user):
    """Get today's freshness report and product availability"""
    try:
        today = datetime.now().date()
        
        # Get today's fresh batches
        fresh_batches = ProductBatch.query.filter(
            db.func.date(ProductBatch.preparation_date) == today
        ).all()
        
        # Get weather-adapted recommendations
        city = request.args.get('city', 'Mumbai')
        weather = get_current_weather(city)
        
        # Generate today's personalized selection
        if current_user.skin_profile:
            daily_selection = get_products_for_weather(weather, current_user.skin_profile)
        else:
            daily_selection = []
        
        freshness_report = {
            'date': today.isoformat(),
            'total_fresh_products': len(fresh_batches),
            'preparation_locations': list(set([batch.preparation_location for batch in fresh_batches])),
            'average_freshness_hours': sum([batch.get_freshness_hours_left() for batch in fresh_batches]) / len(fresh_batches) if fresh_batches else 0,
            'weather_adapted_selection': daily_selection,
            'current_weather': weather,
            'quality_assurance': {
                'all_products_tested': True,
                'organic_certification': True,
                'preparation_time': 'Within 4 hours of delivery',
                'temperature_controlled': True
            }
        }
        
        return jsonify({
            'freshness_report': freshness_report,
            'personalized_message': get_daily_freshness_message(current_user.name),
            'next_preparation_time': get_next_preparation_schedule()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skin-diary', methods=['GET', 'POST'])
@token_required
def skin_diary(current_user):
    """Skin diary to track progress and reactions"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Create a new diary entry (you might want to create a SkinDiary model)
            diary_entry = {
                'user_id': current_user.id,
                'date': datetime.now().date().isoformat(),
                'skin_condition': data.get('skin_condition'),
                'products_used': data.get('products_used', []),
                'skin_feeling': data.get('skin_feeling'),
                'breakouts': data.get('breakouts', False),
                'sensitivity': data.get('sensitivity', False),
                'notes': data.get('notes', ''),
                'photos': data.get('photos', []),  # For progress tracking
                'sleep_hours': data.get('sleep_hours'),
                'stress_level': data.get('stress_level'),
                'water_intake': data.get('water_intake')
            }
            
            # Store in database (implement SkinDiary model if needed)
            
            return jsonify({
                'message': 'Diary entry saved successfully',
                'entry_id': f"diary_{datetime.now().strftime('%Y%m%d')}",
                'insights': generate_skin_insights(diary_entry)
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:  # GET request
        try:
            # Get diary entries for the last 30 days
            # This would fetch from SkinDiary model
            
            mock_entries = [
                {
                    'date': (datetime.now() - timedelta(days=i)).date().isoformat(),
                    'skin_condition': random.choice(['excellent', 'good', 'average', 'poor']),
                    'mood': random.choice(['happy', 'neutral', 'stressed'])
                } for i in range(7)
            ]
            
            return jsonify({
                'diary_entries': mock_entries,
                'progress_summary': {
                    'total_entries': 45,
                    'improvement_trend': 'positive',
                    'consistent_days': 30,
                    'best_performing_products': ['Aloe-Chia Gel', 'Rose Water Toner']
                }
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/community-tips', methods=['GET'])
def get_community_tips():
    """Get skincare tips and success stories from the community"""
    try:
        community_content = {
            'daily_tips': [
                {
                    'tip': 'Apply products on slightly damp skin for better absorption',
                    'category': 'application',
                    'user': 'SkincareLover23',
                    'likes': 45
                },
                {
                    'tip': 'Store your fresh products in the refrigerator for extra cooling effect',
                    'category': 'storage',
                    'user': 'FreshSkinFan',
                    'likes': 38
                },
                {
                    'tip': 'Use cucumber eye patches while doing your morning yoga',
                    'category': 'lifestyle',
                    'user': 'WellnessWarrior',
                    'likes': 52
                }
            ],
            'success_stories': [
                {
                    'title': 'My 30-day Freskin transformation',
                    'preview': 'From dull to glowing skin with consistent fresh products...',
                    'user': 'GlowGetter',
                    'duration': '30 days',
                    'before_after': True
                },
                {
                    'title': 'How I finally found products that work for sensitive skin',
                    'preview': 'After years of reactions, Freskin\'s gentle formulas...',
                    'user': 'SensitiveSkinSurvivor',
                    'duration': '45 days',
                    'before_after': False
                }
            ],
            'seasonal_advice': {
                'current_season': 'summer',
                'tips': [
                    'Switch to lighter gels and hydrating mists',
                    'Use clay masks twice a week to control oil',
                    'Don\'t skip moisturizer even if you have oily skin'
                ]
            }
        }
        
        return jsonify({
            'community_content': community_content,
            'featured_ingredient': get_featured_ingredient_of_week(),
            'diy_tip': get_weekly_diy_tip()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/referral-program', methods=['GET', 'POST'])
@token_required
def referral_program(current_user):
    """Referral program for users to invite friends"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            friend_email = data.get('friend_email')
            
            if not friend_email:
                return jsonify({'error': 'Friend email is required'}), 400
            
            # Generate referral code
            referral_code = f"FRESH{current_user.id}{random.randint(100, 999)}"
            
            # Send referral invitation
            send_referral_invitation(friend_email, current_user.name, referral_code)
            
            return jsonify({
                'message': 'Referral invitation sent successfully',
                'referral_code': referral_code,
                'reward': 'Both you and your friend get ₹200 off your next order!'
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:  # GET request
        try:
            referral_stats = {
                'total_referrals': random.randint(0, 15),
                'successful_referrals': random.randint(0, 8),
                'pending_referrals': random.randint(0, 3),
                'total_rewards_earned': random.randint(0, 2000),
                'current_referral_code': f"FRESH{current_user.id}LOVE",
                'referral_rewards': [
                    {'friend_name': 'Sarah K.', 'reward': 200, 'date': '2024-06-10'},
                    {'friend_name': 'Priya M.', 'reward': 200, 'date': '2024-06-08'}
                ]
            }
            
            return jsonify({
                'referral_stats': referral_stats,
                'program_details': {
                    'friend_discount': '₹200 off first order',
                    'your_reward': '₹200 credit',
                    'additional_benefits': 'Extra eco-points for both'
                }
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Helper functions for the new features

def get_daily_freshness_message(user_name):
    """Generate personalized daily freshness message"""
    messages = [
        f"Good morning {user_name}! Today's products were prepared at 5 AM with fresh ingredients from our partner farms.",
        f"Hello {user_name}! Your skincare selection is ready - made with love and zero preservatives!",
        f"Fresh morning to you {user_name}! Today's batch includes seasonal ingredients perfect for your skin.",
        f"Rise and shine {user_name}! Your chemical-free skincare routine is prepared and on its way!"
    ]
    return random.choice(messages)

def get_next_preparation_schedule():
    """Get next preparation schedule information"""
    next_prep = datetime.now() + timedelta(hours=18)  # Next day's preparation
    return {
        'next_preparation': next_prep.strftime('%Y-%m-%d %H:%M'),
        'cut_off_time': (datetime.now() + timedelta(hours=2)).strftime('%H:%M'),
        'message': 'Order by cut-off time to get tomorrow\'s fresh batch'
    }

def generate_skin_insights(diary_entry):
    """Generate insights based on skin diary entry"""
    insights = []
    
    if diary_entry.get('breakouts'):
        insights.append("Consider using our clay-neem purifying mask this week")
    
    if diary_entry.get('skin_feeling') == 'dry':
        insights.append("Switch to our richer moisturizers for better hydration")
    
    if diary_entry.get('stress_level', 0) > 7:
        insights.append("High stress detected - our lavender-chamomile evening routine might help")
    
    if diary_entry.get('sleep_hours', 8) < 6:
        insights.append("Low sleep affects skin repair - try our overnight treatment masks")
    
    return insights

def get_featured_ingredient_of_week():
    """Get featured natural ingredient information"""
    ingredients = [
        {
            'name': 'Turmeric',
            'benefits': 'Anti-inflammatory, brightening, antibacterial',
            'origin': 'Kerala organic farms',
            'fun_fact': 'Used in Indian beauty rituals for over 4000 years',
            'best_for': 'Acne-prone and dull skin'
        },
        {
            'name': 'Rose Water',
            'benefits': 'Toning, hydrating, pH balancing',
            'origin': 'Kashmir rose gardens',
            'fun_fact': 'Takes 60 roses to make 1 ml of pure rose water',
            'best_for': 'All skin types, especially sensitive'
        }
    ]
    return random.choice(ingredients)

def get_weekly_diy_tip():
    """Get DIY skincare tip"""
    tips = [
        {
            'title': 'Ice Cube Facial',
            'description': 'Wrap ice in cloth and gently massage face for 2 minutes to reduce puffiness',
            'best_time': 'Morning before applying products'
        },
        {
            'title': 'Face Yoga',
            'description': '5 minutes of facial exercises daily can improve circulation and firmness',
            'best_time': 'Evening during your skincare routine'
        }
    ]
    return random.choice(tips)

def send_referral_invitation(friend_email, referrer_name, referral_code):
    """Send referral invitation email"""
    try:
        subject = f"{referrer_name} wants you to try Freskin - Fresh skincare delivered daily!"
        body = f"""
        Hi there!
        
        Your friend {referrer_name} thinks you'd love Freskin - India's first daily fresh skincare delivery service!
        
        🌿 What makes Freskin special:
        • 100% preservative-free products made fresh daily
        • Natural ingredients from local organic farms  
        • Personalized for your skin type
        • Delivered fresh to your doorstep
        
        🎁 Special offer for you:
        Use code {referral_code} and get ₹200 off your first order!
        
        Join thousands who've already transformed their skin with fresh, chemical-free skincare.
        
        Start your fresh skin journey: [Download App Link]
        
        Fresh regards,
        Team Freskin
        
        P.S. Your friend {referrer_name} gets rewarded too when you make your first order!
        """
        
        # Email sending logic here
        print(f"Referral invitation sent to {friend_email}")
        
    except Exception as e:
        print(f"Error sending referral invitation: {e}")

# Add this to the end of your existing app.py file

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        initialize_sample_data()
    app.run(debug=True)

#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging
from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        try:
            json=request.get_json()
            user=User(
                username=json['username'],
                image_url=json.get('image_url'),
                bio=json.get('bio')
            )
            user.password_hash=json['password']
            db.session.add(user)
            db.session.commit()
            session['user_id']=user.id
            return user.to_dict(only=('id', 'username', 'image_url', 'bio',)), 201
        except Exception as e:
            return {'error': f'{e}'}, 422

class CheckSession(Resource):
    def get(self):
        user=User.query.filter(User.id==session.get('user_id')).first()
        if user:
            return user.to_dict(only=('id', 'username', 'image_url', 'bio',)), 200
        else:
            return {'error': '401 Not authorized'}, 401

class Login(Resource):
    def post(self):
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return {'error': 'Username and password are required'}, 400
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.authenticate(password):
                session['user_id'] = user.id
                
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }, 200
            else:
                return {'error': 'Invalid username or password'}, 401
        
        except Exception as e:
            print(f"Login error: {str(e)}")
            return {'error': str(e)}, 500

class Logout(Resource):
    def delete(self):
        if session['user_id']:
            session['user_id']=None
            return '', 204
        else:
            return {'error': 'Unauthorized: No active session'}, 401
    

class RecipeIndex(Resource):
    def get(self):
        if not session['user_id']:
            return {'error': 'Unauthorized: Please log in'}, 401

        user_id=session['user_id']
        user_recipes=Recipe.query.filter_by(user_id=user_id).all()

        recipes_data=[recipe.to_dict(rules=('-user.recipes',)) for recipe in user_recipes]
        return jsonify(recipes_data), 200
        # return jsonify([recipe.to_dict(rules=('-user.recipes',)) for recipe in user_recipes]), 200

    def post(self):
        if not session['user_id']:
            return {'error': 'Unauthorized: Please log in'}, 401
        
        user_id=session['user_id']

        try:
            data=request.get_json()

            new_recipe=Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )

            db.session.add(new_recipe)
            db.session.commit()

            return new_recipe.to_dict(rules=('-user.recipes',)), 201

        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
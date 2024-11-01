from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules=('-recipes.user',)
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String, unique=True, nullable=False)
    _password_hash=db.Column(db.String)
    image_url=db.Column(db.String)
    bio=db.Column(db.String)

    def __repr__(self):
        return f"User {self.id}, {self.username}"

    recipes=db.relationship('Recipe', back_populates='user')

    @validates('username')
    def validate_name(self, key, name):
        if not name:
            raise ValueError('Username must be present')
        return name

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hash is not accessible directly')

    @password_hash.setter
    def password_hash(self, password):
        password_hash=bcrypt.generate_password_hash(
            password.encode('utf-8')
        )
        self._password_hash=password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8')
        )


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    serialize_rules=('-user.recipes',)
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String, nullable=False)
    instructions=db.Column(db.String, nullable=False)
    minutes_to_complete=db.Column(db.Integer)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'))
    user=db.relationship('User', back_populates='recipes')

    @validates('title')
    def validate_title(self, key, title):
        if not title:
            raise ValueError('The title must be present')
        return title

    @validates('instructions')
    def validate_instructions(self, key, instruction):
        if not instruction:
            raise ValueError('Instructions must be present!')
        if len(instruction) < 50:
            raise ValueError('Instructions should be atleast 50 characters long.')
        return instruction
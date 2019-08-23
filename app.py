from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "sddasds as dd d saa sdsa "
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '3cbaed865e28c1'
app.config['MAIL_PASSWORD'] = '580f849ebea5da'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Db created")

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("DB dropped")


@app.cli.command("db_seed")
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class K',
                   home_star='Sol',
                   mass=4.867e24,
                   radius=3760,
                   distance=67.24e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.972e24,
                   radius=3959,
                   distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='William',
                     last_name='Herschel',
                     email='foo@m.com',
                     password='poo')

    db.session.add(test_user)
    db.session.commit()
    print("Done add db foo")


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/simple')
def simple():
    return jsonify(message='Hello again 2'), 200


@app.route('/not_found')
def not_found():
    return jsonify(message='Not found'), 404

@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if (age < 18):
        return jsonify(message=f'sorry {name} too young'), 401
    else:
        return jsonify(message=f'{name} welcome!'), 200


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if (age < 18):
        return jsonify(message=f'sorry {name} too young'), 401
    else:
        return jsonify(message=f'{name} welcome!'), 200


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result.data)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email exists'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created"), 201

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login suceeded", access_token=access_token)
    else:
        return jsonify(message="Bad email or assword"), 401

@app.route('/get_pass/<string:email>', methods=['GET'])
def get_pass(email: str):
        user = User.query.filter_by(email=email).first()
        if user:
            msg = Message("your pass is reset",
                          sender="Me@you.com",
                          recipients=[email])
            mail.send(msg)
        return jsonify(message="Password sent")

@app.route('/retrieve_pass/<string:email>', methods=['POST'])
def retrieve_pass(email: str):
        user = User.query.filter_by(email=email).first()
        if user:
            msg = Message("your planetary password is " + user.password, sender="admin@admin.test", recipients=[email])
            mail.send(msg)
            return jsonify(message="Password sent to: " + email)
        else:
            return jsonify(message="Email does not exist")

@app.route('/planet_details')

# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run()

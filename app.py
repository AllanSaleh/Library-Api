from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Column, ForeignKey, Table
from datetime import date
from flask_marshmallow import Marshmallow #Importing Marshmallow class
from marshmallow import ValidationError

app = Flask(__name__) #Instantiating our Flask app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db' #Connecting a sqlite db to our flask app

# Create a base class for our models
class Base(DeclarativeBase):
  pass
  # you could add your own configuration

# Instantiate your SQLAlchemy database
db = SQLAlchemy(model_class = Base)
ma = Marshmallow()

# Initialize my extension onto my Flask app
db.init_app(app) #adding the db to the app
ma.init_app(app)

loan_books = Table(
    'loan_books',
    Base.metadata,
    Column('loan_id', ForeignKey('loans.id')),
    Column('book_id', ForeignKey('books.id'))
)

class Users(Base):
  __tablename__ = 'users'

  id: Mapped[int] = mapped_column(primary_key=True)
  first_name: Mapped[str] = mapped_column(String(250), nullable=False)
  last_name: Mapped[str] = mapped_column(String(250), nullable=False)
  email: Mapped[str] = mapped_column(String(350), nullable=False, unique=True)
  password: Mapped[str] = mapped_column(String(150), nullable=False)
  DOB: Mapped[date] = mapped_column(Date, nullable=True)
  address: Mapped[str] = mapped_column(String(500), nullable=True)
  role: Mapped[str] = mapped_column(String(30), nullable=False)

  loans: Mapped[list['Loans']] = relationship('Loans', back_populates='user')

class Loans(Base):
    __tablename__ = 'loans'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, nullable=True)
    deadline: Mapped[date] = mapped_column(Date, nullable=True)
    return_date: Mapped[date] = mapped_column(Date, nullable=True)

    user: Mapped['Users'] = relationship('Users', back_populates='loans')
    books: Mapped[list['Books']] = relationship("Books",secondary=loan_books, back_populates='loans')
   
class Books(Base):
  __tablename__ = 'books'

  id: Mapped[int] = mapped_column(primary_key=True)
  title: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
  genre: Mapped[str] = mapped_column(String(360), unique=True, nullable=False)
  age_category: Mapped[str] = mapped_column(String(120), nullable=False)
  publish_date: Mapped[date] = mapped_column(Date, nullable=True)
  author: Mapped[str] = mapped_column(String(500), nullable=True)

  loans: Mapped[list['Loans']] = relationship("Loans",secondary=loan_books, back_populates='books')

class UserSchema(ma.SQLAlchemyAutoSchema):
  class Meta:
    model = Users #Creates a schema that validates the data as defined by our Users Model

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# CREATE USER ROUTE
@app.route('/users', methods=['POST'])
def create_user():
  try:
    # get my user data - responsibility for my client
    data = user_schema.load(request.json) #JSON -> Python
  except ValidationError as e:
    return jsonify(e.messages), 400 #Returning the error as a response so the client can see whats wrong with the status code
  
  # Create a User object from my user data
  # new_user = Users(first_name=data['first_name'],)
  new_user = Users(**data)
  # add User to session
  db.session.add(new_user)
  # commit to session
  db.session.commit()
  #Python -> JSON
  return user_schema.jsonify(new_user), 201 #Successful creation status code

# READ USERS ROUTE
@app.route("/users", methods=["GET"]) #Endpoint to get user information
def read_users():
  users = db.session.query(Users).all()
  return users_schema.jsonify(users), 200 #Returns the list of users as JSON and HTTP status 200

# Read Individual User - using a Dynamic Endpoint
@app.route('/users/<int:user_id>', methods=['GET'])
def read_user(user_id):
  user = db.session.get(Users, user_id)
  return user_schema.jsonify(user), 200

# Delete a User
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
  # db.session.query(Users).where(Users.id == user_id).delete()
  user = db.session.get(Users, user_id)
  if not user:
    return jsonify({"error":"User not found"}), 404
  db.session.delete(user)
  db.session.commit()
  return jsonify({"message": f"Successfully deleted user {user_id}"}), 200

#UPDATE A USER
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
  #Query the user by id
  user = db.session.get(Users, user_id) #Query for our user to update
  if not user: #Checking if I got a user with that id
    return jsonify({"message": "User not found"}), 404 
  #Validate and Deserialize the updates that they are sending in the body of the request
  try:
    user_data = user_schema.load(request.json)
  except ValidationError as e:
    return jsonify({"message": e.messages}), 400
  # for each of the values that they are sending, we will change the value of the queried object

  # if user_data['email']:
  #   user.email = user_data["email"]

  for key, value in user_data.items():
    setattr(user, key, value) #setting object, Attribute, value to replace
  # commit the changes
  db.session.commit()
  # return a response
  return user_schema.jsonify(user), 200

with app.app_context():
  db.create_all()
  # creates all tables defined by our models in the context of the app's configuration and db

app.run(debug=True)
# Finally, we run our Flask app


# Install Marshmallow
# pip install flask-marshmallow marshmallow-sqlalchemy



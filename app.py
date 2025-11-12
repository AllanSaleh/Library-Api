from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Date
from datetime import date

app = Flask(__name__) #Instatiating our Flask app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db' #Connecting a sqlite db to our flask app

# Create a base class for our models
class Base(DeclarativeBase):
  pass
  # you could add your own configuration

# Instantiate your SQLAlchemy database
db = SQLAlchemy(model_class = Base)

# Initialize my extension onto my Flask app
db.init_app(app) #adding the db to the app

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
  
with app.app_context():
  db.create_all()
  # creates all tables defined by our models in the context of the app's configuration and db

app.run()
# Finally, we run our Flask app

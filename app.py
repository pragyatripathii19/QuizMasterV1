from flask import Flask, render_template, request,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
import config
from models import models
from controllers import routes






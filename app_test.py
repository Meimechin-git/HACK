from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_moment import Moment
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, Post, Comment
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import bcrypt
import re
import os

# Flask-Loginの設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # ログインページへのリダイレクト

# 起動処理
app = Flask(__name__)
moment = Moment(app)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# データベースの自動生成
with app.app_context():
    db.create_all()

# Userモデルに必要なメソッドを追加
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    def get_id(self):
        return str(self.id)

# ユーザーのロード関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ルートのエンドポイント
@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', type1_posts=get_type1_posts(), type2_posts=get_type2_posts())
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_moment import Moment
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, Post, Comment
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import bcrypt
import re
import os



#起動処理
app = Flask(__name__)
moment = Moment(app)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
#データベースの自動生成
with app.app_context():
    db.create_all()

# Flask-Loginの設定----------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ユーザーのロード関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#-----------------------------------------------------------------------------


#ルートのエンドポイント
@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', type1_posts=get_type1_posts(), type2_posts=get_type2_posts())
#製品集収集処理
def get_type1_posts():
    type1_posts = Post.query.filter_by(type=1).order_by(Post.id.desc()).all()
    for type1_post in type1_posts:
        type1_post.title = type1_post.title[0:9]+"…" if len(type1_post.title)>20 else type1_post.title
        type1_post.content = type1_post.content[0:51]+"…" if len(type1_post.content)>51 else type1_post.content
    return type1_posts
#要望集収集処理
def get_type2_posts():
    type2_posts = Post.query.filter_by(type=2).order_by(Post.id.desc()).all()
    for type2_post in type2_posts:
        type2_post.title = type2_post.title[0:9]+"…" if len(type2_post.title)>20 else type2_post.title
        type2_post.content = type2_post.content[0:51]+"…" if len(type2_post.content)>51 else type2_post.content
    return type2_posts



#製品集のエンドポイント
@app.route('/products',methods=['GET'])
def products():
    return render_template('products.html', type1_posts=get_type1_posts())



#要望集のエンドポイント
@app.route('/requests',methods=['GET'])
def requests():
    return render_template('requests.html', type1_posts=get_type2_posts())



#サインアップページのエンドポイント
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('アカウントが作成されました。ログインしてください。')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('そのユーザー名は既に使用されています。別の名前をお試しください。')
            return redirect(url_for('signup'))
    return render_template('signup.html')



#ログインページのエンドポイント
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw((password.encode('utf-8')), user.password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash('無効なユーザー名またはパスワードです。')
        return redirect(url_for('login'))
    return render_template('login.html')
#ログアウト処理
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))



#投稿詳細ページのエンドポイント
@app.route('/post/<int:post_id>', methods=['GET'])
def post_detail(post_id):
    post = Post.query.get(post_id)
    post.content = url_link(post.content)
    for comment in post.comments :
        comment.content = url_link(comment.content)
    if post.url == 'NULL':
        post.url = ''

    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('post_detail.html', post=post, comments=comments)
#コメント処理
@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    new_comment = Comment(content=content, post_id=post_id, user_id=session['user_id'])
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post_id))
#URL処理
def url_link(content):
    pattern = r'(https?://[^\s]+)'
    return re.sub(pattern, r'<a href="\1" target="_blank">\1</a>', content).replace("\n", "<br>")


#新規投稿作成ページのエンドポイント
@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if 'user_id' not in session:
        flash('新しい投稿を作るためにログインしてください')
        return redirect(url_for('login'))
    if request.method == 'POST':
        post_type = int(request.form['type'])
        title = request.form['title']
        content = request.form['content']
        url = request.form['url'] if len(request.form['url']) != 0 else 'NULL'
        if url != 'NULL' and url[0:27] != 'https://discord.com/oauth2/':
            flash('ディスコードボットのURLを入れてください')
            return redirect(url_for('new_post'))
        new_post = Post(title=title ,type=post_type ,content=content, url=url, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('new_post.html')



#個人投稿詳細ページのエンドポイント
@app.route('/my_posts', methods=['GET'])
def my_posts():
    if 'user_id' not in session:
        flash('ログインしてください。')
        return redirect(url_for('login'))
    user_id = session['user_id']
    type1_posts = Post.query.filter_by(type=1).filter_by(user_id=user_id).all()
    for type1_post in type1_posts:
        type1_post.title = type1_post.title[0:20]+"…" if len(type1_post.title)>20 else type1_post.title
        type1_post.content = type1_post.content[0:41]+"…" if len(type1_post.content)>41 else type1_post.content
    type2_posts = Post.query.filter_by(type=2).filter_by(user_id=user_id).all()
    for type2_post in type2_posts:
        type2_post.title = type2_post.title[0:20]+"…" if len(type2_post.title)>20 else type2_post.title
        type2_post.content = type2_post.content[0:41]+"…" if len(type2_post.content)>41 else type2_post.content
    return render_template('my_posts.html', type1_posts=type1_posts, type2_posts=type2_posts)
    


#投稿編集ページのエンドポイント
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get(post_id)
    if post.url == 'NULL':
        post.url = ''
    if 'user_id' not in session or post.user_id != session['user_id']:
        flash('この投稿を編集する権限がありません。')
        return redirect(url_for('my_posts'))
    if request.method == 'POST':
        new_post_type = int(request.form['type'])
        new_title = request.form['title']
        new_content = request.form['content']
        new_url = request.form['url'] if len(request.form['url']) != 0 else 'NULL'
        if new_url != 'NULL' and new_url[0:27] != 'https://discord.com/oauth2/':
            flash('ディスコードボットのURLを入れてください')
            return redirect(url_for('edit_post', post_id=post_id))
        post.post_type = new_post_type
        post.title = new_title
        post.content = new_content
        post.url = new_url
        post.updated_at = datetime.utcnow()
        db.session.commit()
        flash('投稿が更新されました。')
        return redirect(url_for('my_posts'))

    return render_template('edit_post.html', post=post)
#投稿削除処理
@app.route('/delete_post/<int:post_id>', methods=['POST', 'GET'])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if 'user_id' not in session or post.user_id != session['user_id']:
        flash('この投稿を削除する権限がありません。')
        return redirect(url_for('my_posts'))
    db.session.delete(post)
    db.session.commit()
    flash('投稿が削除されました。')
    return redirect(url_for('my_posts'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_exception(e):
    db.session.rollback()  # 必要に応じてロールバック
    flash('エラーが発生しました。')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=False)
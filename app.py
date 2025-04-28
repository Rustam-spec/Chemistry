from flask import Flask, render_template, request, redirect, url_for, flash  #Это импортирует все функции из модулей Flask
from flask_sqlalchemy import SQLAlchemy #Это импортирует функцию SQLAlchemy из модуля flask_sqlalchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required  #Это импортирует функции
from werkzeug.security import generate_password_hash, check_password_hash  #Это импортирует функции для хеширования паролей


app = Flask(__name__) #Создаёт экземпляр класса Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newflask.db' #Указывает базу данных
app.config["SECRET_KEY"] = "abc" #Это ключ для защиты от CSRF-атак
db = SQLAlchemy(app) #Создаёт экземпляр класса SQLAlchemy

login_manager = LoginManager() #Создаёт экземпляр класса LoginManager
login_manager.init_app(app) #Это инициализирует LoginManager

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Проверка на уникальность имени пользователя
        if Users.query.filter_by(username=username).first():
            flash("Пользователь с таким именем уже существует.")
            return redirect(url_for("register"))

        # Создание нового пользователя
        user = Users(username=username,
                     is_admin=True if username == "admin_user" else False,
                     password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("sign_up.html")

@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)

@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')    

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/forums')
def forums():
    posts = Post.query.all()
    return render_template('forums.html', posts=posts)

@app.route('/create', methods=['POST', 'GET'])
@login_required  # Убедитесь, что только авторизованные пользователи могут добавлять посты
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        
        # Цензурируем текст
        censored_title = censor_text(title)
        censored_text = censor_text(text)
        
        post = Post(title=censored_title, text=censored_text)

        try:
            db.session.add(post)
            db.session.commit()
            flash('Пост успешно добавлен!', 'success')  # Сообщение об успехе
            return redirect('/')
        except Exception as e:
            flash(f'При добавлении статьи произошла ошибка: {str(e)}', 'error')  # Сообщение об ошибке
            return redirect(url_for('create'))  # Перенаправление обратно на страницу создания поста

    return render_template('create.html')  # Отображаем форму добавления поста

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get("username")).first()
        if user and check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route('/theory')
def theory():
    return render_template('theory.html')

@app.route('/experiments')
def experiments():
    return render_template('experiments.html')

@app.route('/calc')
def calc():
    return render_template('calc.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    posts = Post.query.all()
    return render_template('admin_dashboard.html', posts=posts)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required  # Убедитесь, что только авторизованные пользователи могут удалять посты
def delete_post(post_id):
    post = Post.query.get(post_id)
    
    if post:
        db.session.delete(post)
        db.session.commit()
        flash('Пост успешно удален!', 'success')
    else:
        flash('Пост не найден!', 'error')

    return redirect(url_for('index'))  # Перенаправить на страницу со всеми постами

#Цензура
# Пример списка нецензурных слов
BAD_WORDS = ['плохое_слово1', 'плохое_слово2', 'плохое_слово3']

def censor_text(text):
    for word in BAD_WORDS:
        text = text.replace(word, '*' * 3)  # Заменяем слово на звездочки #len(word)
    return text
if __name__ == '__main__':
    app.run(debug=True)
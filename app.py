
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request,flash,redirect,url_for
import click
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Length,EqualTo,Email
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user
import os
import random
from dotenv import load_dotenv
app = Flask(__name__)
load_dotenv()

app.config.update(
    DEBUG=True,
    SECRET_KEY= os.getenv('SECRET_KEY','dev-default-key-123456'),
    SQLALCHEMY_DATABASE_URI= os.getenv('DATABASE_URL','sqlite:///' + os.path.join(app.root_path,'data.db')),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=True,
)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

#表单
class LoginForm(FlaskForm):
    username = StringField('用户名  ',
                           validators=[
                               DataRequired(message='用户名不能为空'),
                               Length(min=2, max=20,message="长度必须保持在2-20字符之间"),
                           ],
                        )
    password = PasswordField('密码  ' ,
                             validators=[
                                 DataRequired(message='密码不能为空'),
                                ],
                            )
    remember = BooleanField(' 记住我')
    submit = SubmitField('登录')
    submit1 = SubmitField('前往注册')
class RegisterForm(FlaskForm):
    username = StringField('用户名  ',
                           validators=[
                               DataRequired(message='用户名不能为空'),
                               Length(min=2, max=20,message="长度必须保持在2-20字符之间"),
                           ],
                        )
    password = PasswordField('密码  ' ,
                             validators=[
                                 DataRequired(message='密码不能为空'),
                                 Length(min=8, max=20,message="长度必须保持在8-20字符之间"),
                                ],
                            )
    password2 = PasswordField('确认密码',
                              validators=[
                                  DataRequired(message='请确认密码'),
                                  EqualTo('password',message='两次密码不一致')
                              ]
    )
    submit = SubmitField('注册')
class SettingsForm(FlaskForm):
    username = StringField('用户名  ',
                           validators=[
                               DataRequired(message='用户名不能为空'),
                               Length(min=2, max=20, message="长度必须保持在2-20字符之间"),
                           ],
                           )
    password = PasswordField('密码  ',
                             validators=[
                                 DataRequired(message='密码不能为空'),
                                 Length(min=8, max=20, message="长度必须保持在8-20字符之间"),
                             ],
                             )
    password2 = PasswordField('确认密码',
                              validators=[
                                  DataRequired(message='请确认密码'),
                                  EqualTo('password', message='两次密码不一致')
                              ]
                              )
    submit = SubmitField('确定')
    submit1 = SubmitField('登出')
class CommentForm(FlaskForm):
    body = StringField('评论内容',
                       validators=[
                           DataRequired(message='评论不可为空'),
                            Length(min=1,max=500,message='长度不可超过500字'),
                       ]
                       )
    submit = SubmitField('确定')
class NoteForm(FlaskForm):
    body = StringField('内容',
                       validators=[
                           DataRequired(message='内容不可为空'),
                           Length(min=10, max=500, message='长度不可超过500字'),
                       ]
                       )
    submit = SubmitField('确定')
#数据库模型

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(8), primary_key=True,)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128),nullable=False)
    is_active = db.Column(db.Boolean,default=True)
    created_at=db.Column(db.DateTime,default=db.func.current_timestamp())#######
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)########################
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)###################
    def __repr__(self):
        return '<User %r>' % self.username
    def get_id(self):
        return self.id
def generate_unique_user_id():
    while True:
        random_num = random.randint(0,99999999)
        user_id = f'{random_num:08d}'
        if not User.query.get(user_id):
            return user_id
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('notes', lazy=True))
    def __repr__(self):
        return '<Note %r>' % self.id
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    def __repr__(self):
        return '<Comment %r>' % self.id
class Knowledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    path = db.Column(db.Text)
    def __repr__(self):
        return '<Knowledge %r>' % self.title

#route
@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    recent_notes = Note.query.order_by(Note.created_at.desc()).limit(5).all()
    return render_template('index.html', recent_notes=recent_notes)

@app.route('/notes/<int:page>')
def notes(page=1):
    pagination = Note.query.order_by(Note.created_at.desc()) \
    .paginate(page=page,per_page=10,error_out=False)
    anotes = pagination.items
    return render_template('notes.html',notes=anotes,pagination=pagination)

@app.route('/articles')
def all_articles():
    return render_template('all_articles.html')

@app.route('/about')
def about():
    if request.method == 'GET':
        info = os.getenv('FLASK_INFO','暂无相关信息')

    return render_template('about.html',info=info)

@app.route('/note/<int:id>',methods=['GET','POST'])
def note(id):
    statu = current_user.is_authenticated
    form = CommentForm()
    if statu:
        if request.method == 'POST' and form.validate():
            flash("评论成功",'success')
            comment =Comment(
                body = form.body.data,
                user = current_user,
                user_id = current_user.id,
                note_id = id,
            )
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('note',id=id))

    elif request.method == 'POST':
        flash("请先登录",'danger')
        return redirect(url_for('note',id=id))
    comments = Comment.query.filter_by(note_id=id).order_by(Comment.created_at.desc()).all()
    return render_template('note.html',note=Note.query.get(id),comments=comments,form=form,statu=statu)

@app.route('/login',methods=['GET','POST'])
def login():
    #如果通过验证了就直接重定向到首页
    if current_user.is_authenticated:#通过返回T，否则是False
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == 'POST':
        if form.submit1.data:
            return redirect(url_for('register'))
        if form.validate():
            user = User.query.filter_by(username=form.username.data).first()###########
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)#####################
                flash('Welcome home, %s!' % form.username.data,'info')
                next_page = request.args.get('next')#####################
                return redirect(next_page) if next_page else redirect(url_for('index'))###################
            else:
                flash('用户名或密码错误','danger')#######################
        else:
            # 表单验证失败时，显示具体错误信息
            for field_name, errors in form.errors.items():
                for error in errors:
                    # 将字段名转换为中文显示
                    if field_name == 'username':
                        field_display = '用户名'
                    elif field_name == 'password':
                        field_display = '密码'
                    else:
                        field_display = field_name

                    flash(f'{field_display}: {error}', 'danger')
    return render_template('login.html',form=form)

@app.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    form = RegisterForm()
    if request.method == 'POST' and form.validate():
        existing_user = User.query.filter( ############################
            (User.username == form.username.data)
        ).first()
        if existing_user:
            if existing_user.username == form.username.data:
                flash('用户名已存在','danger')
            return render_template('register.html',form=form)
        user = User(id=generate_unique_user_id(),username = form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功','success')
        return redirect(url_for('login'))
    else:
        for field_name, errors in form.errors.items():
            for error in errors:
                if field_name == 'username':
                    field_display = '用户名'
                elif field_name == 'password':
                    field_display = '密码'
                elif field_name == 'password2':
                    field_display = '确认密码'
                else:
                    field_display = field_name
                flash(f'{field_display}: {error}', 'danger')
    return render_template('register.html',form=form)

@app.route('/upload',methods=['GET','POST'])
def publish():
    if not current_user.is_authenticated:
        flash("请先登录",'danger')
        return redirect(url_for('login'))
    form = NoteForm()
    if request.method == "POST" and form.validate():
        note = Note(
            body = form.body.data,
            user = current_user,
            user_id = current_user.id,
        )
        db.session.add(note)
        db.session.commit()
        flash('笔记发布成功！','success')
        return redirect(url_for('index'))

    return render_template('publish.html',form=form)

@login_required
@app.route('/settings',methods=['GET','POST'])
def settings():
    form = SettingsForm()
    if request.method == 'GET':
        form.username.data = current_user.username
    if request.method == 'POST':
        if form.submit1.data:
            logout_user()
            flash('成功登出','info')
            return redirect(url_for('index'))
        if form.validate():
            new_username = form.username.data.strip()
            new_password = form.password.data.strip() if form.password.data else None
            if not new_username:
                flash('用户名不能为空！', 'danger')
                return render_template('settings.html', form=form)
            existing_user = User.query.filter(
                User.username == new_username,
                User.id != current_user.id
            ).first()
            if existing_user:
                flash('用户名已存在', 'danger')
                return render_template('settings.html', form=form)
            current_user.username = new_username
            if new_password:
                if check_password_hash(current_user.password_hash,new_password,):
                    flash('与原密码相同','danger')
                    return render_template('settings.html', form=form)
                else:
                    current_user.set_password(new_password)

            try:
                db.session.commit()
                flash('修改成功', 'success')
                # 清除密码字段
                form.password.data = ''
                form.password2.data = ''
            except Exception as e:
                db.session.rollback()
                flash(f"修改失败: {str(e)}", 'danger')
        else:
            # 表单验证失败时也显示错误
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    return render_template('settings.html', form=form)


#tools
@login_manager.user_loader#####################
def load_user(user_id):##############
    return User.query.get(user_id)####################

#command
@app.cli.command()
def initdb():
    with app.app_context():
        db.drop_all()
        db.create_all()
        from sqlalchemy.schema import CreateTable
        print(CreateTable(User.__table__))
        print(CreateTable(Note.__table__))
        print(CreateTable(Comment.__table__))
        click.echo('init db successfully!')

@app.cli.command()
def test_userdb(): #如果函数名字带了下划线，要想使用这个命令时，就必须要将原有的下划线替代为"-"
    with app.app_context():
        admin = User(id=generate_unique_user_id(),username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        click.echo('test_userdb successfully!')

@app.cli.command()
def test_notedb(): #如果函数名字带了下划线，要想使用这个命令时，就必须要将原有的下划线替代为"-"
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            click.echo('请先使用 flask test-userdb 创建admin用户')
            return
        for i in range(25):
            note = Note(
                user_id=admin.id,
                body=f'测试笔记{i+1}:这是第{i+1}条测试笔记'
            )
            db.session.add(note)
        db.session.commit()
        click.echo('test_notedb successfully! 已添加25条测试笔记!')

@app.cli.command()
def test_commentdb():
    with app.app_context():
        note = Note.query.filter_by(id=1).first()
        user = User.query.filter_by(username='admin').first()
        if not note:
            click.echo('请先创建id为1的Note')
            return
        for i in range(10):
            comment = Comment(
                note_id = note.id,
                body =f'测试评论{i+1}:这是第{i+1}条测试评论',
                user =user
            )
            db.session.add(comment)
        db.session.commit()
        click.echo('test_commentdb successfully!')

@app.cli.command()
def read_notedb():
    with app.app_context():
        notes = Note.query.all()
        for note in notes:
            click.echo(note.body)

        click.echo('read_notedb successfully!')

@app.cli.command()
def read_commentdb():
    with app.app_context():
        comments = Comment.query.all()
        for comment in comments:
            click.echo(f"{comment.body}  这条评论属于Note:{comment.note_id}")

        click.echo('read_commentdb successfully!')


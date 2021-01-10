from flaskblog import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


att = db.Table('att',
               db.Column('id', db.Integer, db.ForeignKey('user.id')),
               db.Column('subject_id', db.Integer, db.ForeignKey('subject.subject_id'))
               )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_professor = db.Column(db.Boolean, nullable=False, default=False)
    attendances = db.relationship('Subject', secondary=att,
                                  backref=db.backref('students', lazy='dynamic'))  # many to many
    edit = db.relationship('Edit', backref='author')  # one to many
    book_item = db.relationship('Book_item', backref='owner')  # one to many
    vote = db.relationship('Vote', backref='user')  # one to many

    def __repr__(self):
        return "User('{}', '{}', '{}', '{}')".format(self.username, self.email, self.password, self.is_professor)

    @classmethod
    def professors(cls):
        return cls.query.filter_by(is_professor=True).all()

    @classmethod
    def user_logged_in(cls, current_user):
        return cls.query.filter_by(username=current_user.username).first()

    @classmethod
    def get_user_by_email(cls, form):
        return cls.query.filter_by(email=form.email.data).first()

    @classmethod
    def get_all_users(cls):
        return cls.query.all()


class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(20), unique=True, nullable=False)
    book = db.relationship('Book', backref='subject', uselist=False)  # one to one
    lecture = db.relationship('Lecture', backref='subject')  # one to many

    def __repr__(self):
        return "Subject ('{}')".format(self.subject_name)

    @classmethod
    def get_user_subjects(cls, current_user):
        return cls.query.filter(Subject.students.any(username=current_user.username)).all()

    @classmethod
    def get_subject_or_error(cls, subject_id):
        return cls.query.get_or_404(subject_id)

    @classmethod
    def subject_to_be_modified(cls, mod_sub_id):
        return cls.query.get_or_404(mod_sub_id)


class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(20), unique=True, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), unique=True)  # one to one
    book_item = db.relationship('Book_item', backref='book')  # one to many

    def __repr__(self):
        return "Book ('{}', '{}')".format(self.book_name, self.subject.subject_name)


class Lecture(db.Model):
    lecture_id = db.Column(db.Integer, primary_key=True)
    lecture_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)  # one to many
    edit = db.relationship('Edit', backref='lecture')  # one to many

    def __repr__(self):
        return "Lecture ('{}', '{}', '{}')".format(self.lecture_name, self.subject.subject_name, self.content)

    @classmethod
    def get_lecture_or_error(cls, lecture_id):
        return cls.query.get_or_404(lecture_id)


class Edit(db.Model):
    edit_id = db.Column(db.Integer, primary_key=True)
    edit_name = db.Column(db.String(100), nullable=False)
    edit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    edit_status = db.Column(db.String(100), nullable=False, default='To be approved')
    content = db.Column(db.Text, nullable=False)
    approvals = db.Column(db.Integer, nullable=False, default=0)
    refused = db.Column(db.Integer, nullable=False, default=0)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.lecture_id'), nullable=False)  # one to many
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # one to many
    vote = db.relationship('Vote', backref='edit')  # one to many

    def __repr__(self):
        return "Edit ('{}', '{}', '{}')".format(self.edit_name, self.author.username, self.lecture.lecture_name)

    @classmethod
    def get_edit(cls, edit_id):
        return cls.query.get(edit_id)


class Book_item(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    item_status = db.Column(db.String(100), nullable=False, default='New')
    item_expiring = db.Column(db.DateTime)
    future_owner = db.Column(db.String(100), nullable=False, default='To be assigned')
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)  # one to many
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # one to many

    def __repr__(self):
        return "Edit ('{}', '{}')".format(self.book.book_name, self.owner.username)

    @classmethod
    def item_exchanged(cls, it_id):
        return cls.query.filter_by(item_id=it_id).first()

    @classmethod
    def item_asked_or_error(cls, item_id):
        return cls.query.get_or_404(item_id)


class Vote(db.Model):
    vote_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # one to one
    edit_id = db.Column(db.Integer, db.ForeignKey('edit.edit_id'))  # one to one

    def __repr__(self):
        return "Edit ('{}', '{}')".format(self.user.username, self.edit.edit_name)

    @classmethod
    def all_edit_vote(cls, ed):
        return cls.query.filter_by(edit_id=ed).all()

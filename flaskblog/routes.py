from flask import render_template, url_for, flash, redirect, request
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, EditForm
from flaskblog.models import User, Subject, att, Edit, Lecture, Vote, Book_item, Book
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from wordcloud import WordCloud, ImageColorGenerator
# import matplotlib.pyplot as plt  :library to see preview word cloud
from PIL import Image
import numpy as np
import re
from collections import Counter
from pdf import download

def word_cloud():
    text = ""
    with open('flaskblog/feedback.txt') as f:
        text = ''.join(f.readlines())
    custom_mask = np.array(Image.open("flaskblog/static/assets/img/cloud.png"))
    wc = WordCloud(background_color="black", mask=custom_mask)
    words = re.findall(r'\w+', open('flaskblog/feedback.txt').read())
    words_counter = Counter(words)
    wc.generate_from_frequencies(words_counter)
    image_colors = ImageColorGenerator(custom_mask)
    wc.recolor(color_func=image_colors)
    wc.to_file('flaskblog/static/assets/img/output.png')


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        feedback = open("flaskblog/feedback.txt", "a")
        txt = request.form["feedback"]
        add_txt = "{} \n".format(txt)
        feedback.write(add_txt)
        word_cloud()
    return render_template('index.html', title='Smart Study', menu=True, notification=True)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, menu=True, notification=True)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_user_by_email(form)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Welcome back {}'.format(current_user.username), 'success')
            return redirect(next_page) if next_page else redirect(url_for('ps'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form, menu=True, notification=True)


@app.route("/study_plan")
@login_required
def ps():
    sub = Subject.get_user_subjects(current_user)

    professors = User.professors()

    position = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth']
    len1 = len(sub)
    return render_template('PersonalStudyPlan.html', sub=sub, position=position, profs=professors, len1=len1,
                           title='Personal Study Plan')


@app.route("/books")
@login_required
def books():
    sub = Subject.get_user_subjects(current_user)

    position = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth']
    len1 = len(sub)
    len2 = []
    disabled = []
    status = []
    item = []
    color = []

    for i in range(0, len1):
        len2.append(len(sub[i].book.book_item))
        disabled.append(False)
        status.append(None)
        item.append(None)
        color.append(None)

    for i in range(0, len1):
        for j in range(0, len2[i]):
            c = 'intime'
            if sub[i].book.book_item[j].item_expiring == None:
                sub[i].book.book_item[j].item_expiring = datetime.utcnow()

            if datetime.utcnow() >= sub[i].book.book_item[j].item_expiring:
                if sub[i].book.book_item[j].future_owner == 'To be assigned':
                    sub[i].book.book_item[j].item_status = 'WAITING TO GIVE'
                    c = 'waiting'
                else:
                    sub[i].book.book_item[j].item_status = 'EXCHANGE'
                    c = 'exchange'
            else:
                expiring = datetime.utcnow() + timedelta(days=10)
                if sub[i].book.book_item[j].item_expiring <= expiring:
                    sub[i].book.book_item[j].item_status = 'RUNNING OUT'
                    c = 'runningout'
            color[i] = c
            if sub[i].book.book_item[j].owner_id == current_user.id:
                disabled[i] = True
                future_owner = str(current_user.id)
                item[i] = sub[i].book.book_item[j].item_id
                if sub[i].book.book_item[j].future_owner == future_owner:
                    status[i] = sub[i].book.book_item[j].item_status
                    if sub[i].book.book_item[j].item_status != 'EXCHANGE':
                        status[i] = 'RENEWAL {}'.format(sub[i].book.book_item[j].item_expiring.strftime('%b-%d'))
                        sub[i].book.book_item[j].item_status = status[i]
                        c = 'renewal'
                elif sub[i].book.book_item[j].future_owner == 'To be assigned':
                    status[i] = sub[i].book.book_item[j].item_status
                else:
                    status[i] = sub[i].book.book_item[j].item_status
                    if sub[i].book.book_item[j].item_status != 'EXCHANGE' and sub[i].book.book_item[
                        j].item_status != 'IN TIME':
                        status[i] = 'GIVE {}'.format(sub[i].book.book_item[j].item_expiring.strftime('%b-%d'))
                        sub[i].book.book_item[j].item_status = status[i]
                        c = 'runningout'
                color[i] = c
                break
            else:
                future_owner = str(current_user.id)
                if sub[i].book.book_item[j].future_owner == future_owner:
                    disabled[i] = True
                    if datetime.utcnow() >= sub[i].book.book_item[j].item_expiring:
                        status[i] = 'WAITING'
                    else:
                        status[i] = 'WAITING {}'.format(sub[i].book.book_item[j].item_expiring.strftime('%b-%d'))
                    c = 'waiting'
                    color[i] = c
                    break

    db.session.commit()

    return render_template('Books.html', sub=sub, position=position, len1=len1, disabled=disabled, status=status,
                           item=item, color=color, title='Books')


@app.route("/exchanged/<int:it_id>")
@login_required
def exchanged(it_id):
    user = User.user_logged_in(current_user)
    len_i = len(user.book_item)
    for i in range(0, len_i):
        if user.book_item[i].item_id == it_id:
            break
    item = Book_item.item_exchanged(it_id)
    item.item_expiring = datetime.utcnow() + timedelta(days=130)
    item.item_status = 'IN TIME'
    item.owner_id = int(item.future_owner)
    item.future_owner = 'To be assigned'
    db.session.commit()
    return redirect(url_for('books'))


@app.route("/ask/<int:subject_id>")
@login_required
def ask(subject_id):
    sub = Subject.get_subject_or_error(subject_id)
    len_i = len(sub.book.book_item)
    find = False
    for i in range(0, len_i):
        if sub.book.book_item[i].item_status == 'TO BE ASSIGNED':
            item_id = sub.book.book_item[i].item_id
            item = Book_item.item_asked_or_error(item_id)
            item.owner_id = current_user.id
            item.item_expiring = datetime.utcnow() + timedelta(days=130)
            item.item_status = 'IN TIME'
            find = True
            flash('Book assigned', 'success')
            break
    if not find:
        for i in range(0, len_i):
            if sub.book.book_item[i].future_owner == 'To be assigned':
                item_id = sub.book.book_item[i].item_id
                item = Book_item.item_asked_or_error(item_id)
                item.future_owner = str(current_user.id)
                break
        if datetime.utcnow() >= sub.book.book_item[i].item_expiring:
            flash('You have to wait for the confirmation', 'danger')
        else:
            flash('The book will be available from {}'.format(sub.book.book_item[i].item_expiring.strftime('%Y-%m-%d')),
                  'info')
    db.session.commit()
    return redirect(url_for('ps'))


@app.route("/edits")
@login_required
def edits():
    user = User.user_logged_in(current_user)
    ed = user.edit
    len1 = len(ed)
    return render_template('Edits.html', ed=ed, len1=len1, title='Edits')


@app.route("/status")
@login_required
def status():
    sub = Subject.get_user_subjects(current_user)
    user = User.user_logged_in(current_user)
    users = User.get_all_users()
    books = user.book_item
    ed = user.edit
    len_e = len(ed)
    approvals = 0
    for i in range(0, len_e):
        approvals = approvals + ed[i].approvals * 2 - ed[i].refused
    len_s = len(sub)
    len_u = len(users)
    len_b = len(books)
    return render_template('Status.html', title='Status', notification=True, len_s=len_s, len_e=len_e, len_u=len_u,
                           len_b=len_b, approvals=approvals)


@app.route("/subject/<int:subject_id>/<int:lecture_id>")
@login_required
def subject(subject_id, lecture_id):
    download(subject_id)
    sub = Subject.get_subject_or_error(subject_id)
    lec = sub.lecture
    len1 = len(lec)
    approve = True
    disabled = False
    proposed_edits = [edit.content for edit in lec[lecture_id].edit if edit.edit_status == 'To be approved']
    ed = [edit.edit_id for edit in lec[lecture_id].edit if edit.edit_status == 'To be approved']
    proposed_edit = None if len(proposed_edits) == 0 else proposed_edits[0]
    ed = None if len(proposed_edits) == 0 else ed[0]
    if proposed_edit:
        disabled = True
        v = Vote.all_edit_vote(ed)
        len_v = len(v)
        for k in range(0, len_v):
            if v[k].user_id == current_user.id:
                approve = False
                break
        if approve:
            flash('There is an edit to be voted', 'success')
        else:
            flash('You have already voted this edit', 'danger')
    else:
        approve = False
        flash('Please, propose a modification', 'info')
    link = ""
    if subject_id == 1:
        link = "https://drive.google.com/file/d/1xptx4IwJ5CSUnAC_VMwdqwLwT_MR6y_A/view?usp=sharing"
    elif subject_id == 2:
        link = "https://drive.google.com/file/d/1Z5KEHe6Fx5QckNXpctmtXFO0LsWT5o6W/view?usp=sharing"
    elif subject_id == 3:
        link = "https://drive.google.com/file/d/1omf-91jQLL3AZrXBjIVqUxleIxfJWeb-/view?usp=sharing"
    elif subject_id == 4:
        link = "https://drive.google.com/file/d/1UXbr_UdCE9YmzOZ8o06AgPZOKjT7jvFa/view?usp=sharing"
    return render_template('Subject.html', sub=sub, lec=lec, len1=len1, lecture_id=lecture_id, title='Subject',
                           notification=True, disabled=disabled, proposed_edit=proposed_edit, approve=approve, ed=ed, link=link)


# funziona
@app.route("/vote <int:lecture_id> <int:approve> ")
@login_required
def vote(lecture_id, approve):
    lec = Lecture.get_lecture_or_error(lecture_id)
    ed = lec.edit
    len_ed = len(ed)
    for i in range(0, len_ed):
        if ed[i].edit_status == 'To be approved':
            break

    if current_user.is_professor:
        if approve == 1:
            ed[i].approvals = ed[i].approvals + 20
        else:
            ed[i].refused = ed[i].refused + 20
    else:
        if approve == 1:
            ed[i].approvals = ed[i].approvals + 1
        else:
            ed[i].refused = ed[i].refused + 1
    if ed[i].approvals >= 25:
        ed[i].edit_status = "Validated"
        lec.content = ed[i].content
    if ed[i].refused >= 25:
        ed[i].edit_status = "Refused"
    user_vote = Vote(user_id=current_user.id, edit_id=ed[i].edit_id)
    db.session.add(user_vote)
    db.session.commit()
    flash('Your vote have been register', 'success')
    return redirect(url_for('ps'))


@app.route("/modification <int:mod_sub_id> <int:mod_lec_id> <int:edit_id>", methods=['GET', 'POST'])
@login_required
def modification(mod_sub_id, mod_lec_id, edit_id):
    sub = Subject.subject_to_be_modified(mod_sub_id)
    edit = Edit.get_edit(edit_id)
    lec = sub.lecture[mod_lec_id]
    edits = lec.edit
    form = EditForm()
    leg = lec.lecture_name
    if form.validate_on_submit():
        edit = Edit.get_edit(edit_id)
        if edit:
            if form.content.data == edit.content or form.content.data == lec.content:
                flash('Unchanged content', 'danger')
            else:
                if current_user.is_professor:
                    lec.content = form.content.data
                else:
                    edit = Edit(edit_name=form.title.data, content=form.content.data, author=current_user,
                                lecture=lec)
                db.session.add(edit)
                db.session.commit()
                flash('Your edit has been created!', 'success')
                return redirect(url_for('ps'))
        else:
            if form.content.data == lec.content:
                flash('Unchanged content', 'danger')
            else:
                if current_user.is_professor:
                    lec.content = form.content.data
                else:
                    edit = Edit(edit_name=form.title.data, content=form.content.data, author=current_user,
                                lecture=lec)
                    db.session.add(edit)
                db.session.commit()
                flash('Your edit has been created!', 'success')
                return redirect(url_for('ps'))
    if edit:
        form.content.data = edit.content
    else:
        form.content.data = lec.content
    return render_template('Modification.html', form=form, sub=sub, lec=lec, legend=leg, title='Modification',
                           notification=True, edits=edits, mod_sub_id=mod_sub_id, mod_lec_id=mod_lec_id, edit=edit)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

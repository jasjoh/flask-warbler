import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm, CSRFForm
from models import db, connect_db, User, Message, Like
from werkzeug.exceptions import Unauthorized

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
# toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """Create reference to CSRF Form and ff we're logged in ...
    add curr user to Flask global."""
    if CURR_USER_KEY in session:

        g.user = User.query.get(session[CURR_USER_KEY])

        # g is specific to this to request / response cycle
        # g is gone and recreated with every request
        # (why its in before_request route)
        # g is ALWAYS passed to every template
        # dont have to say user=user
        # session[CURRE_USER_KEY] gives us back user.id
        # When we do User.query.get, gives us a user instance,
        # and store in g.user

    else:
        g.user = None

    # define CSRF Form
    g.csrf_form = CSRFForm()

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    # TODO: Need to update navbar after logout. Should probably do inside
    # the logout method.

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if form.validate_on_submit():
        do_logout()
        flash("Logged Out Successfully", "success")
        return redirect("/")

    flash("Invalid request", 'danger')

    return redirect("/")

##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():

        followed_user = User.query.get_or_404(follow_id)
        flash(f"Sucessfully following {followed_user.username}", "success")
        g.user.following.append(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    flash("Invalid request", 'danger')

    return redirect("/")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():

        followed_user = User.query.get_or_404(follow_id)
        flash(f"Sucessfully unfollowed {followed_user.username}", "success")
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    flash("Invalid request", 'danger')

    return redirect("/")


# TODO: Ask why this doesn't go to /users/<userid>/profile
@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        password = form.password.data

        # verify password
        if User.authenticate(g.user.username, password):

            # password is good, update user data
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data

            db.session.commit()

            return redirect(f"/users/{g.user.id}")

        # invalid password, return error
        else:
            flash("Invalid password. Please try again.", "danger")
            return render_template("users/edit.html", form=form)

    return render_template("users/edit.html", form=form)

@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page.
    """
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():

        do_logout()

        db.session.delete(g.user)
        db.session.commit()

        return redirect("/signup")

    flash("Invalid request", 'danger')

    return redirect("/")

@app.get('/users/<int:user_id>/liked_messages')
def get_liked_messages(user_id):
    """Display liked messages by the user"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/show_liked.html', user=user)


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():

        msg = Message.query.get_or_404(message_id)

        if g.user.id == msg.user_id:

            db.session.delete(msg)
            db.session.commit()
        else:
            flash("Access Unauthorized", 'danger')

        return redirect(f"/users/{g.user.id}")

    flash("Invalid request", 'danger')

    return redirect("/")

@app.post('/messages/<int:message_id>/toggle_like')
def toggle_like(message_id):
    """ Toggle like status of a message and refresh the page. """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    destination = f'/{request.args["page"]}'

    form = g.csrf_form

    if form.validate_on_submit():

        # # TODO: We could potentially abstract this into the model akin to
        # # is_following() / is_followed_by
        # # double check the message isn't owned by the current user
        # if message in g.user.messages:
        #     # message is owned by user - not allowed; redirect back to home
        #     flash("Error: Cannot like own messages.", 'danger')
        #     return redirect(destination)

        # # toggle like status
        # if message in g.user.liked_messages:
        #     g.user.liked_messages.remove(message)
        # else:
        #     g.user.liked_messages.append(message)

        if not g.user.toggle_like(message):
            # message is owned by user - not allowed; redirect back to home
            flash("Error: Cannot like own messages.", 'danger')
            return redirect(destination)

        db.session.commit()

        return redirect(destination)
# TODO: use unauthorize
    # flash("Invalid request", 'danger')
    raise Unauthorized()


##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        messages = (Message
                    .query
                    .filter(db.or_(
                            Message.user_id == g.user.id,
                            Message.user_id.in_(
                                [user.id for user in g.user.following]
                            )
                    ))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response

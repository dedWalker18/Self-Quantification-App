from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()
class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_fname=db.Column(db.String, nullable=False)
    user_lname=db.Column(db.String)


class Tracker(db.Model):
    __tablename__ = "tracker"
    tracker_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id,ondelete="CASCADE"), nullable=False)
    tracker_name = db.Column(db.String, nullable=False)
    tracker_type = db.Column(db.String, nullable=False)
    tracker_description= db.Column(db.String)
    tracker_settings=db.Column(db.String)
    tracker_lastupate=db.Column(db.DateTime)



class Log(db.Model):
    __tablename__ = "log"
    log_id = db.Column(db.Integer, primary_key=True)
    tracker_id = db.Column(db.Integer, db.ForeignKey(Tracker.tracker_id,ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id,ondelete="CASCADE"), nullable=False)
    log_time=db.Column(db.DateTime ,nullable=False)
    log_value=db.Column(db.String,nullable=False)
    log_note=db.Column(db.String)

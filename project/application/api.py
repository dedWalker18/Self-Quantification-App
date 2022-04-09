from flask import Flask, request, render_template, redirect, url_for,g
from flask import make_response
from flask import current_app as app
from flask import session
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func

from flask_restful import Resource, fields, marshal_with, reqparse
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from application.database import *
from application.validations import *
from passlib.hash  import sha256_crypt
import pytz

IST = pytz.timezone('Asia/Kolkata')

#_________________________________________________________________________________________________________


user_parser = reqparse.RequestParser()
user_parser.add_argument("user_id")
user_parser.add_argument("username")
user_parser.add_argument("password")
user_parser.add_argument("user_fname")
user_parser.add_argument("user_lname")

tracker_parser = reqparse.RequestParser()
tracker_parser.add_argument("tracker_id")
tracker_parser.add_argument("user_id")
tracker_parser.add_argument("tracker_name")
tracker_parser.add_argument("tracker_type")
tracker_parser.add_argument("tracker_description")
tracker_parser.add_argument("tracker_settings")

log_parser = reqparse.RequestParser()
log_parser.add_argument("log_id")
log_parser.add_argument("tracker_id")
log_parser.add_argument("user_id")
log_parser.add_argument("log_time")
log_parser.add_argument("log_value")
log_parser.add_argument("log_note")

graph_parser = reqparse.RequestParser()
graph_parser.add_argument("tracker_id")
graph_parser.add_argument("user_id")


#_________________________________________________________________________________________________________
user_output = {
    "user_id": fields.Integer,
    "username": fields.String,
    "user_fname": fields.String,
    "user_lname": fields.String
}

tracker_output = {
    "tracker_id": fields.Integer,
    "user_id": fields.Integer,
    "tracker_name": fields.String,
    "tracker_type": fields.String,
    "tracker_description":fields.String,
    "tracker_settings": fields.String,
    "tracker_lastupate": fields.String
}

log_output= {
    "log_id": fields.Integer,
    "tracker_id": fields.Integer,
    "log_time": fields.String,
    "log_value": fields.String,
    "log_note": fields.String
}

graph_output= {
    "today": fields.String,
    "week": fields.String,
    "month": fields.String
}

error_dict = {
    "U1e": ("USER01", "User Doesn't Exist."),
    "U2e": ("USER02", "Username Already Exist Try Another Username"),
    "U3e": ("USER03", "Username Doesn't Have any Traker."),
    "P1e": ("PASSWORD01", "Wrong Password."),
    "P2e": ("PASSWORD02", "Password Can't Be Empaty."),
    "T1e": ("TRACKER01", "Tracker Doesn't Exist."),
    "T2e": ("TRACKER02", "Tracker Doesn't Have Any Log."),
    "T3e": ("TRACKER03", "Tracker Already Exist."),
    "T4e": ("TRACKER04", "Tracker Doesn't Have any Logs."),
    "T5e": ("TRACKER05", "Multiple Choice Type Tracker can't have Empty Settings."),
    "L1e": ("LOG01", "Log Doesn't Exist."),
    "L2e": ("LOG01", "Log Already Exist.")
}

class UserSignInAPI(Resource):

    @marshal_with(user_output)
    def post(self):
        args = user_parser.parse_args()
        username=args.get("username",None)
        password=args.get("password",None)
        if password is None:
            raise BusinessValidationError(400,error_code=error_dict["P2e"][0],error_msg=error_dict["P2e"][1])
        user=User.query.filter_by(username=username).first()
        if user:
            if sha256_crypt.verify(password,user.password):
                return user
            else:
                raise BusinessValidationError(400,error_code=error_dict["P1e"][0],error_msg=error_dict["P1e"][1])
        else:
            raise BusinessValidationError(400,error_code=error_dict["U1e"][0],error_msg=error_dict["U1e"][1])


class RegistrationAPI(Resource):

    @marshal_with(user_output)
    def post(self):
        args = user_parser.parse_args()
        username=args.get("username", None)
        user=db.session.query(User).filter(User.username==username).first()
        if user is not None:
            raise BusinessValidationError(400,error_code=error_dict["U2e"][0],error_msg=error_dict["U2e"][1])
        else:
            password=args.get("password", None)
            if password:
                password = sha256_crypt.encrypt(password)
            else:
                raise BusinessValidationError(400,error_code=error_dict["P2e"][0],error_msg=error_dict["P2e"][1])
            user_fname=args.get("user_fname", None)
            user_lname=args.get("user_lname", None)
            user=User(username=username,password=password,user_fname=user_fname,user_lname=user_lname)
            db.session.add(user)
            db.session.commit()
            return user

class UserAPI(Resource):
    @marshal_with(user_output)
    def get(self):
        args = user_parser.parse_args()
        user_id=args.get("user_id", None)
        user=User.query.filter_by(user_id=user_id).first()
        if user:
            return user
        else:
            raise BusinessValidationError(400,error_code=error_dict["U1e"][0],error_msg=error_dict["U1e"][1])

class TrackerAPI(Resource):

    @marshal_with(tracker_output)
    def get(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        user=User.query.filter_by(user_id=user_id).first()
        if user:
            if tracker_id is None:
                trackerlist=Tracker.query.filter_by(user_id=user_id).all()
                if len(trackerlist)>0:
                    return trackerlist
                else:
                    raise BusinessValidationError(400,error_code=error_dict["U3e"][0],error_msg=error_dict["U3e"][1])
            else:
                tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
                if tracker is not None:
                    return tracker
                else:
                    raise BusinessValidationError(400,error_code=error_dict["T1e"][0],error_msg=error_dict["T1e"][1])
        else:
            raise BusinessValidationError(400,error_code=error_dict["U1e"][0],error_msg=error_dict["U1e"][1])


    @marshal_with(tracker_output)
    def post(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_name=args.get("tracker_name", None)
        tracker_type=args.get("tracker_type", None)
        tracker_description=args.get("tracker_description", None)
        tracker_settings=args.get("tracker_settings", None)
        if tracker_type=='Multiple Choice' and tracker_settings is None:
            raise BusinessValidationError(400,error_code=error_dict["T5e"][0],error_msg=error_dict["T5e"][1])
        if tracker_type=='Boolean':
            tracker_settings='Yes,No'
        user=User.query.filter_by(user_id=user_id).first()
        if user:
            tracker=Tracker.query.filter((Tracker.tracker_name==tracker_name) & (Tracker.user_id==user_id)).first()
            if tracker:
                raise BusinessValidationError(400,error_code=error_dict["T3e"][0],error_msg=error_dict["T3e"][1])
            else:
                tracker=Tracker(user_id=user_id,tracker_name=tracker_name,tracker_type=tracker_type,tracker_settings=tracker_settings,tracker_description=tracker_description)
                db.session.add(tracker)
                db.session.commit()
                return tracker
        else:
            raise BusinessValidationError(400,error_code=error_dict["U1e"][0],error_msg=error_dict["U1e"][1])

    @marshal_with(tracker_output)
    def put(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        tracker_name=args.get("tracker_name", None)
        tracker_description=args.get("tracker_description", None)
        user=User.query.filter_by(user_id=user_id).first()
        if user:
            tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
            if tracker:
                tracker.tracker_name=tracker_name
                tracker.tracker_description=tracker_description
                db.session.commit()
                return tracker
            else:
                raise BusinessValidationError(400,error_code=error_dict["T1e"][0],error_msg=error_dict["T1e"][1])
        else:
            raise BusinessValidationError(400,error_code=error_dict["U1e"][0],error_msg=error_dict["U1e"][1])

    @marshal_with(tracker_output)
    def delete(self):
        args = tracker_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        user=User.query.filter_by(user_id=user_id).first()
        if user:
            tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
            if tracker:
                db.session.delete(tracker)
                db.session.commit()
                raise BusinessValidationSuccessful()
            else:
                raise BusinessValidationError(400,error_code=error_dict["T1e"][0],error_msg=error_dict["T1e"][1])
        else:
            raise BusinessValidationError(400,error_code=error_dict["U1e"][0],error_msg=error_dict["U1e"][1])

class LogAPI(Resource):

    @marshal_with(log_output)
    def get(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        log_id=args.get("log_id", None)
        if log_id==None:
            loglist=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id)).all()
            if len(loglist)>0:
                return loglist
            else:
                raise BusinessValidationError(400,error_code=error_dict["T4e"][0],error_msg=error_dict["T4e"][1])
        else:
            log=Log.query.filter((Log.log_id==log_id) & (Log.user_id==user_id) & (Log.tracker_id==tracker_id)).first()
            if log:
                return log
            else:
                raise BusinessValidationError(400,error_code=error_dict["L1e"][0],error_msg=error_dict["L1e"][1])

    @marshal_with(log_output)
    def post(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        t=args.get("log_time", None)
        log_time = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")
        log_value=args.get("log_value", None)
        log_note=args.get("log_note", None)
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker:
            log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time==log_time)).first()
            if log:
                raise BusinessValidationError(400,error_code=error_dict["L2e"][0],error_msg=error_dict["L2e"][1])
            else:
                log=Log(user_id=user_id,tracker_id=tracker_id,log_time=log_time,log_value=log_value,log_note=log_note)
                if tracker.tracker_lastupate:
                    if log_time>tracker.tracker_lastupate:
                        tracker.tracker_lastupate=log_time
                else:
                    tracker.tracker_lastupate=log_time
                db.session.add(log)
                db.session.commit()
                return log
        else:
            raise BusinessValidationError(400,error_code=error_dict["T1e"][0],error_msg=error_dict["T1e"][1])

    @marshal_with(log_output)
    def put(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        log_id=args.get("log_id", None)
        t=args.get("log_time", None)
        log_time = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")
        log_value=args.get("log_value", None)
        log_note=args.get("log_note", None)
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker:
            log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_id==log_id)).first()
            if log:
                if tracker.tracker_lastupate:
                    if log_time>tracker.tracker_lastupate:
                        tracker.tracker_lastupate=log_time
                else:
                    tracker.tracker_lastupate=log_time
                log.log_time=log_time
                log.log_value=log_value
                log.log_note=log_note
                db.session.commit()
                return log
            else:
                raise BusinessValidationError(400,error_code=error_dict["L1e"][0],error_msg=error_dict["L1e"][1])
        else:
            raise BusinessValidationError(400,error_code=error_dict["T1e"][0],error_msg=error_dict["T1e"][1])

    @marshal_with(log_output)
    def delete(self):
        args = log_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        log_id=args.get("log_id", None)
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker:
            log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_id==log_id)).first()
            if log:
                db.session.delete(log)
                db.session.commit()
                log=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id)).order_by(Log.log_time.desc()).first()
                if log:
                    tracker.tracker_lastupate=log.log_time
                else:
                    tracker.tracker_lastupate=None
                db.session.commit()
                raise BusinessValidationSuccessful()
            else:
                raise BusinessValidationError(400,error_code=error_dict["L1e"][0],error_msg=error_dict["L1e"][1])
        else:
            raise BusinessValidationError(400,error_code=error_dict["T1e"][0],error_msg=error_dict["T1e"][1])


class GraphAPI(Resource):

    @marshal_with(graph_output)
    def get(self):
        args = graph_parser.parse_args()
        user_id=args.get("user_id", None)
        tracker_id=args.get("tracker_id", None)
        d={'today':'No','week':'No','month':'No'}
        tracker=Tracker.query.filter((Tracker.user_id==user_id) & (Tracker.tracker_id==tracker_id)).first()
        if tracker:
            datetoday=datetime.datetime.now(IST).replace(hour=0,minute=0,second=0,microsecond=0)
            weekstart=datetoday-datetime.timedelta(days=datetoday.weekday())
            monthstart=datetoday.replace(day=1)
            if tracker.tracker_type=='Numerical':
                loglisttoday=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=datetoday)).order_by(Log.log_time.asc()).all()
                if len(loglisttoday)>0:
                    x=[]
                    y=[]
                    for i in loglisttoday:
                        x.append(i.log_time)
                        y.append(i.log_value)
                    plt.plot_date(x,y,'b-')
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_today.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["today"]='Yes'
                loglistweek=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=weekstart)).order_by(Log.log_time.asc()).all()
                if len(loglistweek)>0:
                    x=[]
                    y=[]
                    for i in loglistweek:
                        x.append(i.log_time)
                        y.append(i.log_value)
                    plt.plot_date(x,y,'b-')
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_week.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["week"]='Yes'
                loglistmonth=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=monthstart)).order_by(Log.log_time.asc()).all()
                if len(loglistmonth)>0:
                    x=[]
                    y=[]
                    for i in loglistmonth:
                        x.append(i.log_time)
                        y.append(i.log_value)
                    plt.plot_date(x,y,'b-')
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_month.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["month"]='Yes'
            elif tracker.tracker_type=='Multiple Choice':
                settings=tracker.tracker_settings
                settings=settings.split(',')
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=datetoday)&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    plt.pie(data, labels = name)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_today.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["today"]='Yes'
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=weekstart)&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    plt.pie(data, labels = name)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_week.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["week"]='Yes'
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=monthstart)&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    plt.pie(data, labels = name)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_month.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["month"]='Yes'
            elif tracker.tracker_type=='Boolean':
                settings=tracker.tracker_settings
                settings=settings.split(',')
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=datetoday)&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    x=range(len(data))
                    plt.xticks(x,name)
                    plt.bar(x,data)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_today.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["today"]='Yes'
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=weekstart)&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    x=range(len(data))
                    plt.xticks(x,name)
                    plt.bar(x,data)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_week.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["week"]='Yes'
                data=[]
                name=[]
                for i in settings:
                    count=Log.query.filter((Log.user_id==user_id) & (Log.tracker_id==tracker_id) & (Log.log_time>=monthstart)&(Log.log_value==i)).count()
                    if count>0:
                        data.append(count)
                        name.append(i)
                if len(data)>0:
                    x=range(len(data))
                    plt.xticks(x,name)
                    plt.bar(x,data)
                    photoname='static/'+str(user_id)+'_'+str(tracker_id)+'_month.png'
                    plt.savefig(photoname)
                    plt.clf()
                    d["month"]='Yes'
            return d
        return d
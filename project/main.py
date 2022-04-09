from flask import request, render_template, redirect, url_for,flash
from flask import current_app as app
from application.database import *
from flask import session
from  datetime import datetime
from application.api import *
import requests
import pytz


IST = pytz.timezone('Asia/Kolkata')

from flask_restful import Resource, Api
app = None
api = None
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy()
db.init_app(app)
api = Api(app)
app.app_context().push()
app.secret_key = 'secret key'

db.create_all()
db.session.commit()

api.add_resource(UserSignInAPI, '/api/usersignin')
api.add_resource(RegistrationAPI, '/api/registration')
api.add_resource(UserAPI, '/api/user')
api.add_resource(TrackerAPI, '/api/tracker')
api.add_resource(LogAPI, '/api/log' )
api.add_resource(GraphAPI, '/api/graph' )


@app.route('/')
def home_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    else:
        return render_template("home.html")

@app.route('/login', methods=["GET","POST"])
def login_page():
    if 'user_id' in session:
            return redirect(url_for('dashboard_page'))
    else:
        if request.method == "GET":
            return render_template("login.html")
        elif request.method == "POST":
            d={}
            d['username'] = request.form.get('username',None)
            d['password'] =  request.form.get('password',None)
            data=requests.post('http://127.0.0.1:8080/api/usersignin', d).json()
            if 'user_id' in data:
                session['user_id']=data['user_id']
                session['user_fname']=data['user_fname']
                return redirect(url_for('dashboard_page'))
            elif 'error_code' in data:
                session.pop('_flashes', None)
                flash(data['error_message'])
                return redirect(url_for('login_page'))

@app.route('/register', methods=["GET","POST"])
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    else:
        if request.method == "GET":
            return render_template("register.html")
        elif request.method == "POST":
            d={}
            d['username'] = request.form.get('username',None)
            d['password'] =  request.form.get('password',None)
            d['user_fname'] = request.form.get('fname',None)
            d['user_lname'] =  request.form.get('lname',None)
            data=requests.post('http://127.0.0.1:8080/api/registration', d).json()
            if 'user_id' in data:
                session.pop('_flashes', None)
                flash('Registration Successful')
                return redirect(url_for('login_page'))
            elif 'error_code' in data:
                session.pop('_flashes', None)
                flash(data['error_message'])
                return redirect(url_for('register_page'))


@app.route('/dashboard')
def dashboard_page():
    if 'user_id' in session:
        if request.method == "GET":
            d={}
            d['user_id']=session['user_id']
            user_fname=session['user_fname']
            flag=True
            data=requests.get('http://127.0.0.1:8080/api/tracker', d).json()
            if  "error_code" in data:
                flag=False
            else:
                for i in data:
                    if i['tracker_lastupate']==None:
                        i['tracker_lastupate']='No Logs'
                    else:
                        tracker_lastupate=i['tracker_lastupate'][:-3]
                        tracker_lastupate = datetime.datetime.strptime(tracker_lastupate, "%Y-%m-%d %H:%M")
                        i['tracker_lastupate']=tracker_lastupate.strftime('%Y-%m-%d %I:%M %p')
            return render_template("dashboard.html",trackers=data,user_fname=user_fname,flag=flag)
    else:
        return redirect(url_for('login_page'))

@app.route('/tracker',methods=["GET","POST"])
def tracker_page():
    if 'user_id' in session:
        if request.method == "GET":
            type=request.args.get('type',None)
            tracker_id=request.args.get('t_id',None)
            if type is not None and tracker_id is not None:
                if type=='delete':
                    d={}
                    d['user_id']=session['user_id']
                    d['tracker_id']=tracker_id
                    data=requests.delete('http://127.0.0.1:8080/api/tracker',params=d).json()
                    if 'code' in data:
                        session.pop('_flashes', None)
                        flash('Tracker has Been Delete.')
                        return redirect(url_for('dashboard_page'))
                    elif 'error_code' in data:
                        session.pop('_flashes', None)
                        flash(data['error_message'])
                        return redirect(url_for('dashboard_page'))
                elif type=='update':
                    d={}
                    d['user_id']=session['user_id']
                    d['tracker_id']=tracker_id
                    data=requests.get('http://127.0.0.1:8080/api/tracker', d).json()
                    if 'tracker_id' in data:
                        return render_template("update tracker.html",tracker=data)
                    elif 'error_code' in data:
                        session.pop('_flashes', None)
                        flash(data['error_message'])
                        return redirect(url_for('dashboard_page'))

            elif type==None and tracker_id is not None:
                d={}
                d['user_id']=session['user_id']
                d['tracker_id']=tracker_id
                d['log_id']=None
                trackerdata=requests.get('http://127.0.0.1:8080/api/tracker', d).json()
                if 'tracker_id' in trackerdata:
                    logdata=requests.get('http://127.0.0.1:8080/api/log', d).json()
                    flag=False
                    if 'error_code' in logdata:
                        session.pop('_flashes', None)
                        flash(logdata['error_message'])
                        return redirect(url_for('dashboard_page'))
                    else:
                        user_fname=session['user_fname']
                        tracker_name=trackerdata['tracker_name']
                        tracker_type=trackerdata['tracker_type']
                        if 'log_id' in logdata[0]:
                            flag=True
                            # graphdata=graph(tracker_id,session['user_id'])
                            graphdata=requests.get('http://127.0.0.1:8080/api/graph', d).json()
                            for i in logdata:
                                log_time=i['log_time'][:-3]
                                log_time = datetime.datetime.strptime(log_time, "%Y-%m-%d %H:%M")
                                i['log_time']=log_time.strftime('%Y-%m-%d %I:%M %p')

                        return render_template("tracker.html",user_fname=user_fname,logs=logdata,tracker_id=tracker_id,tracker_name=tracker_name,flag=flag,tracker_type=tracker_type,graphdata=graphdata)
            else:
                return render_template("add tracker.html")

        elif request.method == "POST":
            type=request.args.get('type',None)
            tracker_id=request.args.get('t_id',None)
            if type is not None and tracker_id is not None:
                d={}
                d['user_id']=session['user_id']
                d['tracker_id']=tracker_id
                d['tracker_name'] = request.form.get('name',None)
                d['tracker_description'] = request.form.get('description',None)
                data=requests.put('http://127.0.0.1:8080/api/tracker', d).json()
                if 'tracker_id' in data:
                    session.pop('_flashes', None)
                    flash('Tracker has Been Upated Succesfully.')
                    return redirect(url_for('dashboard_page'))
                elif 'error_code' in data:
                    session.pop('_flashes', None)
                    flash(data['error_message'])
                    return redirect(url_for('dashboard_page'))
            else:
                d={}
                d['user_id']=session['user_id']
                d['tracker_name'] = request.form.get('name',None)
                d['tracker_type'] =  request.form.get('type',None)
                d['tracker_description'] = request.form.get('description',None)
                d['tracker_settings'] =  request.form.get('settings',None)
                data=requests.post('http://127.0.0.1:8080/api/tracker', d).json()
                if 'tracker_id' in data:
                    session.pop('_flashes', None)
                    flash('Tracker has Been Added Succesfully.')
                    return redirect(url_for('dashboard_page'))
                elif 'error_code' in data:
                    session.pop('_flashes', None)
                    flash(data['error_message'])
                    return redirect(url_for('tracker_page'))
    else:
        return redirect(url_for('login_page'))


@app.route('/log',methods=["GET","POST"])
def log_page():
    if 'user_id' in session:
        if request.method == "GET":
            type=request.args.get('type',None)
            tracker_id=request.args.get('t_id',None)
            tracker_type=request.args.get('t_type',None)
            log_id=request.args.get('l_id',None)
            if type is not None and tracker_id is not None and log_id is not None:
                if type=='delete':
                    d={}
                    d['user_id']=session['user_id']
                    d['tracker_id']=tracker_id
                    d['log_id']=log_id
                    data=requests.delete('http://127.0.0.1:8080/api/log',params=d).json()
                    if 'code' in data:
                        session.pop('_flashes', None)
                        flash('Log Has Been Deleted')
                        return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))
                    elif 'error_code' in data:
                        session.pop('_flashes', None)
                        flash(data['error_message'])
                        return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))
                elif type=='update':
                    d={}
                    d['user_id']=session['user_id']
                    d['tracker_id']=tracker_id
                    d['log_id']=log_id
                    logdata=requests.get('http://127.0.0.1:8080/api/log', d).json()
                    if 'log_id' in logdata:
                        log_time= logdata['log_time']
                        log_time=log_time.split(' ')
                        log_time=log_time[0]+'T'+log_time[1][:-3]
                        trackerdata=requests.get('http://127.0.0.1:8080/api/tracker', d).json()
                        settings=trackerdata['tracker_settings'].split(',')
                        tracker_type=trackerdata['tracker_type']
                        return render_template("update log.html",log=logdata,tracker_type=tracker_type,tracker_id=tracker_id,log_time=log_time,settings=settings)
                    elif 'error_code' in logdata:
                        session.pop('_flashes', None)
                        flash(logdata['error_message'])
                        return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))

            elif tracker_id is not None and tracker_type is not None and log_id is None :
                time=datetime.datetime.now(IST)
                time=time.strftime('%Y-%m-%dT%H:%M')
                d={}
                d['user_id']=session['user_id']
                d['tracker_id']=tracker_id
                data=requests.get('http://127.0.0.1:8080/api/tracker', d).json()
                settings=data['tracker_settings'].split(',')
                return render_template("add log.html",tracker_id=tracker_id,tracker_type=tracker_type,time=time,settings=settings)

        elif request.method == "POST":
            type=request.args.get('type',None)
            tracker_id=request.args.get('t_id',None)
            log_id=request.args.get('l_id',None)
            tracker_type=request.args.get('t_type',None)
            if type is not None and tracker_id is not None and log_id is not None:
                d={}
                d['user_id']=session['user_id']
                d['tracker_id']=tracker_id
                d['log_id']=log_id
                log_time= request.form['log_time']
                log_time=log_time.split('T')
                log_time=log_time[0]+' '+log_time[1]
                d['log_time']=log_time
                d['log_value'] = request.form.get('log_value',None)
                d['log_note'] = request.form.get('log_note',None)
                data=requests.put('http://127.0.0.1:8080/api/log', d).json()
                if 'log_id' in data:
                    session.pop('_flashes', None)
                    flash('Log has Been Upated Succesfully.')
                    return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))
                elif 'error_code' in data:
                    session.pop('_flashes', None)
                    flash(data['error_message'])
                    return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))
            else:
                d={}
                d['user_id']=session['user_id']
                d['tracker_id']=tracker_id
                log_time= request.form.get('log_time',None)
                log_time=log_time.split('T')
                log_time=log_time[0]+' '+log_time[1]
                d['log_time']=log_time
                d['log_value'] = request.form.get('log_value',None)
                d['log_note'] = request.form.get('log_note',None)
                data=requests.post('http://127.0.0.1:8080/api/log', d).json()
                if 'log_id' in data:
                    session.pop('_flashes', None)
                    flash('Log has Been Added Succesfully.')
                    return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))
                elif 'error_code' in data:
                    session.pop('_flashes', None)
                    flash(data['error_message'])
                    return redirect(url_for('tracker_page')+'?t_id='+str(tracker_id))
    else:
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout_page():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == "__main__" :
    app.run(host="0.0.0.0", debug=True, port=8080)
from flask import Flask,render_template,redirect,request,jsonify
import ibm_db
import smtplib 
import pandas
import pickle
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
import joblib
import time
import sklearn
import requests


conn = ibm_db.connect("DATABASE=bludb; HOSTNAME=8e359033-a1c9-4643-82ef-8ac06f5107eb.bs2io90l08kqb1od8lcg.databases.appdomain.cloud; PORT= 30120; SECURITY =SSL;UID=plf17642; PWD=NwfEGbS5rPNsE2V1;", '', '')
API_KEY = "os-DKidt6FFwJ-7vmhI9kiHODviQ16N2bxjCYz-6cFVX"

app = Flask(__name__)
model = pickle.load(open('D:\IBM Project\Rainfall.pkl','rb'))


@app.route('/')
def home():
    return render_template('home.html', msg="")

@app.route('/addhome',methods=['POST','GET'])
def addhome():
    # signup data
    if request.method == 'POST':
        name = request.form['uname']
        email = request.form['Email']
        cpass = request.form['psw']

        sel_sql = "SELECT * FROM USER WHERE EMAIL=?"
        stmt = ibm_db.prepare(conn, sel_sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        acc = ibm_db.fetch_assoc(stmt)

        if acc:
            return render_template('home.html',msg="Existing User so Login") 
        else:
            ins_sql = "INSERT INTO USER VALUES(?,?,?)"
            pstmt = ibm_db.prepare(conn, ins_sql)
            ibm_db.bind_param(pstmt, 1, name)
            ibm_db.bind_param(pstmt, 2, email)
            ibm_db.bind_param(pstmt, 3, cpass)

            ibm_db.execute(pstmt)
            return render_template('dashboard.html')
    return "hhhh"

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'POST':
        cemail = request.form['lemail']
        cpass = request.form['psw']

        sel_sql = "SELECT * FROM USER WHERE EMAIL=?"
        stmt = ibm_db.prepare(conn, sel_sql)
        ibm_db.bind_param(stmt, 1, cemail)
        ibm_db.execute(stmt)
        acc = ibm_db.fetch_assoc(stmt)

        if acc:
            if (str(cpass)) == str(acc['PASSWORD'].strip()):
                return render_template("dashboard.html")
            else:
                return render_template("home.html", msg="Invalid E-Mail or Password")
        else:
            return render_template("home.html", msg="Not yet registered, please signup")
    else:
        return render_template("home.html")

@app.route('/forgetpass',methods=['POST','GET'])
def forgetpass():
    if request.method == 'POST':
        cemail = request.form['email']
        sel_sql = "SELECT * FROM USER WHERE EMAIL=?"
        stmt = ibm_db.prepare(conn, sel_sql)
        ibm_db.bind_param(stmt, 1, cemail)
        ibm_db.execute(stmt)
        acc = ibm_db.fetch_assoc(stmt)

        if acc:
            PASS_sql = "SELECT PASSWORD FROM USER WHERE EMAIL=?"
            stmtt = ibm_db.prepare(conn, PASS_sql)
            ibm_db.bind_param(stmtt, 1, cemail)
            ibm_db.execute(stmtt)
            accC = ibm_db.fetch_assoc(stmtt)

            return render_template('home.html', passs="YOUR PASSWORD : "+str(accC['PASSWORD'].strip())) 
        else :
            return render_template('home.html', passs="No Email found!")

@app.route('/predict',methods=["POST","GET"])
def predict():
    #reading the inputs given by the user
    input_feature=[x for x in request.form.values()]
    del input_feature[1]
    print(input_feature)
    features_values=[np.array(input_feature)] 
    token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
    API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
    mltoken = token_response.json()["access_token"]

    header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}

    # NOTE: manually define and pass the array(s) of values to be scored in the next line
    payload_scoring = {"input_data": [{"field": [['Location', 'MinTemp', 'MaxTemp', 'WindDirection']], "values": [[x for x in input_feature]]}]}

    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/c098e76c-a9a8-4b66-90a3-9df74fbcb621/predictions?version=2022-11-18', json=payload_scoring,
    headers={'Authorization': 'Bearer ' + mltoken})
    print("Scoring response")
    print(response_scoring.json())
    predictions = response_scoring.json()
    pred = predictions['predictions'][0]['values'][0][1]

    if(pred == "yes"):
        return render_template("Chances.html")
    else:
        return render_template("No chances.html")


if __name__ == '__main__':
    app.run(debug=True)
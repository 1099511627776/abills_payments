#!/usr/bin/python
import cgi
import cgitb
import json
import dbmanager
import os
import datetime
import hashlib

cgitb.enable()
operator = 17
dbmanager.init()

####errno : 1 - unknown user
####errno : 2 - error making payment
####errno : 3 - transaction exists
####errno : 4 - transaction not exists
####errno : 5 - bad chacksum

def process(form):
    aResult = ""
    if 'command' in form:
	cmd = form["command"].value
	if(cmd == 'check'):
	    if('account' in form) and ('txn_id' in form):
		uid = int(form["account"].value)
		txnid = form["txn_id"].value
		uid_result = dbmanager.check_user(uid)
		txn_result = dbmanager.check_tid(txnid)
		if (uid_result['result'] == 'ok') and (txn_result['result'] != 'ok'):
			aResult = """<?xml version="1.0" encoding="UTF-8"?>
			<response>
			    <osmp_txn_id>%(txn_id)s</osmp_txn_id>
			    <result>0</result>
				<fields>
				    <field1 name="disp1">%(login)s</field1>
				    <field2 name="disp2">%(fio)s</field2>
				    <field3 name="disp3">%(address)s</field3>
				</fields>
				<comment></comment>
			</response>""" % {'txn_id':txnid,'login':uid_result['id'],'address':uid_result['addr'],'fio':uid_result['fio']}
		elif (uid_result['result'] != 'ok') and (txn_result['result'] != 'ok'):
			aResult = """<?xml version="1.0" encoding="UTF-8"?>
			<response>
			    <osmp_txn_id>%(txn_id)s</osmp_txn_id>
			    <result>5</result>
			    <comment>Unknown user</comment>
			</response>""" % {'txn_id':txnid}
		else:
			aResult = """<?xml version="1.0" encoding="UTF-8"?>
			<response>
			    <osmp_txn_id>%(txn_id)s</osmp_txn_id>
			    <result>300</result>
			    <comment>Already payed</comment>
			</response>""" % {'txn_id':txnid}
	elif(cmd == "pay"):
	    if ('account' in form) and ('txn_id' in form) and ('sum' in form):
		uid = int(form['account'].value)
		tid = form['txn_id'].value
		summ = float(form['sum'].value)
		ip=os.environ['REMOTE_ADDR']
		result = dbmanager.pay(uid,operator,summ,tid,ip)
		if(result['result'] == 'ok'):
		    aResult = """<?xml version="1.0" encoding="UTF-8"?>
			<response>
			    <osmp_txn_id>%(tid)s</osmp_txn_id>
			    <prv_txn>%(uid)s</prv_txn>
			    <prv_txn_date>%(date)s</prv_txn_date>
			    <sum>%(sum)s</sum>
			    <result>0</result>
			    <comment>OK</comment>
			</response>""" % {'tid':tid,'sum':summ,'uid':uid,'date':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
	    else:
		aResult = ""
    return aResult

print "Content-type: text/xml\n";
form = cgi.FieldStorage()

aResult = process(form)

print aResult

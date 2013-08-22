#!/usr/bin/python
import cgi
import cgitb
import json
import dbmanager
import os
import datetime
import hashlib
import math
from xml.dom.minidom import *

cgitb.enable(format='text')
operator = 17
dbmanager.init()

####errno : 1 - unknown user
####errno : 2 - error making payment
####errno : 3 - transaction exists
####errno : 4 - transaction not exists
####errno : 5 - bad chacksum

def process(xml_data):
    dt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    aResult = ""
    xml = parseString(xml_data)
    check = xml.getElementsByTagName('Check')
    pay = xml.getElementsByTagName('Payment')
    confirm = xml.getElementsByTagName('Confirm')
    if(check != []):
	servie_id = xml.getElementsByTagName('ServiceId')[0]
	account = xml.getElementsByTagName('Account')[0].firstChild.nodeValue
	#print account.nodeValue
	result = dbmanager.check_user(account)
	deposit = dbmanager.get_deposit2(account)
	if(deposit < 0):
	    deposit = -deposit
	else:
	    deposit = 0
	#print result
	if(result['result'] == 'ok'):
	    aResult = """
		<Response>
		    <StatusCode>0</StatusCode>
		    <StatusDetail>Ok</StatusDetail>
		    <DateTime>%(dt)s</DateTime>
		    <AccountInfo>
			<Name>%(fio)s</Name>
			<Address>%(addr)s</Address>
			<Balance>%(deposit)2g</Balance>
			
		    </AccountInfo>
		</Response>""" % {'fio':result['fio'],'addr':result['addr'],'deposit':math.ceil(deposit),'dt':dt }
	else:
	    aResult = """
		<Response>
		    <StatusCode>-1</StatusCode>
		    <StatusDetail>%(result)s</StatusDetail>
		</Response>""" % {'result':result['status']}
    elif(pay != []):
	service_id = int(xml.getElementsByTagName('ServiceId')[0].firstChild.nodeValue)
	uid = int(xml.getElementsByTagName('Account')[0].firstChild.nodeValue)
	pkey = xml.getElementsByTagName('OrderId')[0].firstChild.nodeValue
	summ = float(xml.getElementsByTagName('Amount')[0].firstChild.nodeValue)
	datt = xml.getElementsByTagName('DateTime')[0].firstChild.nodeValue
	ip = os.environ['REMOTE_ADDR']
	#print service_id, uid, operator, summ, datt
	result = dbmanager.pay_order(uid,operator,summ,pkey,ip,datt)
	if(result['result'] == 'ok'):
		aResult = """
			<Response>
			    <StatusCode>0</StatusCode>
			    <StatusDetail>Order Created</StatusDetail>
			    <DateTime>%(dt)s</DateTime>
			    <PaymentId>%(tid)s</PaymentId>
			</Response>""" % {'dt':dt,'tid':pkey}
	else:
		aResult = """
			<Response>
			    <StatusCode>-1</StatusCode>
			    <StatusDetail>%(result)s</StatusDetail>
			</Response>""" % {'result':result['status']}
    elif( confirm != []):
	service_id = int(xml.getElementsByTagName('ServiceId')[0].firstChild.nodeValue)
	payment_id = xml.getElementsByTagName('PaymentId')[0].firstChild.nodeValue
	result = dbmanager.confirm_order(payment_id)
	if(result['result'] == 'ok'):
		aResult = """
			<Response>
			    <StatusCode>0</StatusCode>
			    <StatusDetail>Confirmed</StatusDetail>
			    <DateTime>%(dt)s</DateTime>
			    <OrderDate>%(ddt)s</OrderDate>
			</Response>""" % {'dt':dt,'ddt':result['date']}
	else:
		aResult = """
			<Response>
			    <StatusCode>-1</StatusCode>
			    <StatusDetail>%(status)s</StatusDetail>
			    <DateTime>%(dt)s</DateTime>
			    <OrderDate>%(ddt)s</OrderDate>
			</Response>""" % {'dt':dt,'status':result['status'],'ddt':result['date']}
    return aResult

print "Content-type: text/xml\n";
storage = cgi.FieldStorage()
xml_data = storage.file.read()
aResult = process(xml_data)

print aResult

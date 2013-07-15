import MySQLdb as mdb
import datetime

_cfg = {
    'host':'127.0.0.1',
    'user':'payments',
    'pwd':'password',
    'db':'abills'
}

db = None

def init():
    global _cfg
    global db
    db = mdb.connect(_cfg['host'],_cfg['user'],_cfg['pwd'],_cfg['db'])
    cur = db.cursor()
    cur.execute("SET NAMES utf8")
    return cur.fetchone()

def check_user(uid):
    global db
    cur = db.cursor()
    sql = """
    SELECT 
        id,
        u.uid,
        gid,
        fio,
        phone,
        concat(address_street,',',address_build,',',address_flat)
    FROM users u 
        INNER JOIN users_pi upi ON u.uid = upi.uid WHERE u.bill_id = %s """
    if(cur.execute(sql,uid) != 0):
    data = cur.fetchone()
    return {
        'result':'ok',
        'id':data[0],
        'uid':data[1],
        'gid':data[2],
        'fio':data[3],
        'phone':data[4],
        'addr':data[5]
    }
    else:
    return {'result':'error','errno':1,'status':'unknown user'}

def get_deposit(uid):
    global db
    sql = "SELECT deposit FROM bills WHERE uid = %s"
    cur = db.cursor()
    cur.execute(sql,uid)
    data = cur.fetchone()
    return data[0]

def get_deposit2(billid):
    global db
    sql = "SELECT deposit FROM bills WHERE id = %s"
    cur = db.cursor()
    cur.execute(sql,billid)
    data = cur.fetchone()
    return data[0]

def set_deposit(uid,deposit):
    global db
    sql = "UPDATE bills SET deposit = %s WHERE id = %s"
    cur = db.cursor()
    return cur.execute(sql,(deposit,uid))

def get_uid(billid):
    global db
    sql = "SELECT uid FROM users WHERE bill_id = %s"
    cur = db.cursor()
    cur.execute(sql,billid)
    data = cur.fetchone()
    return data[0]

def check_tid(tid):
    global db
    sql = """ SELECT count(*) FROM payments WHERE ext_id = %s """
    cur = db.cursor()
    if(cur.execute(sql,"tr_id:"+str(tid)) != 0):
    data = cur.fetchone()
    if(data[0] != 0):
        return {'result':'ok','tid-count':data[0]}
    else:
        return {'result':'error','tid-count':data[0],'errno':3}
        #return {'result':'error','tid':data[0],'errno':4}
    else:
    return {'result':'erorr','status':'db_error','errno':2}

def pay(billid,operator,sum,tid,ip,datt = None):
    uid = get_uid(billid);
    deposit = get_deposit2(billid)
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """INSERT INTO payments(bill_id,uid,date,sum,amount,last_deposit,ext_id,inner_describe,aid,ip,reg_date) 
              values (%s     ,%s ,%s  ,%s ,%s    ,%s          ,%s    ,%s            ,%s ,INET_ATON(%s),%s)"""
    cur = db.cursor()
    if(cur.execute(sql,(billid,uid,dt,sum,sum,deposit,"tr_id:"+str(tid),"",operator,ip,dt)) == 1):
    res = set_deposit(billid,deposit + sum)
#   print res
    if res == 1:
        return {'result':'ok'}
    else:
        return {'result':'error','status':'err_depo','errno':2}
    else:
    return {'result':'error','status':'fatal','errno':2}

#init()
#uid = 10
#data = check_user(uid)
#print "checkuser: ",data
#print "deposit", get_deposit(uid)
#print "deposit", get_billid(uid)
#pay(uid,2,100.01,32113,'192.168.0.1')
#print set_deposit(uid,100.01)

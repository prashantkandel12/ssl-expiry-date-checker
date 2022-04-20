import eel
import sqlite3
import validators
import socket
import ssl
import datetime

# start a database connection
con = sqlite3.connect('urls.db')
mycursor = con.cursor()

# initialize desktop app
eel.init('web')


def close_callback(route, websockets):
    if not websockets:
        con.close()
        exit()

# function to check URLs expiry status and save to database


@eel.expose
def checkURL(address):
    try:
        hostname = address.replace("https://", "")
        hostname = hostname.replace("http://", "")
        ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'

        context = ssl.create_default_context()
        sslConn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=hostname,
        )
        sslConn.connect((hostname, 443))
        ssl_info = sslConn.getpeercert()
        expiry = datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)
        check = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        mycursor.execute("update urls set expire='%s',checked='%s' where url='%s'" % (
            expiry, check, address))
        con.commit()
        eel.setStatus("Checked "+address)
    except Exception as e:
        eel.setStatus("Error: cannot connect to "+address)


@eel.expose
def checkAllURLs():
    eel.setStatus("Checking status of all URLs")
    sql = "select * from urls order by url"
    mycursor.execute(sql)
    resultData = mycursor.fetchall()
    tableData = []
    for row in resultData:
        checkURL(row[0])
    eel.setStatus("Checking Complete")

# function to check remaining days


def ssl_expires_in(expires, buffer_days=14):
    remaining = expires - datetime.datetime.utcnow()
    if remaining < datetime.timedelta(days=0):
        return ("<b class='red'>Expired %s days ago<b>" % remaining.days)
    elif remaining < datetime.timedelta(days=buffer_days):
        return ("<b class='orange'>Expiring in %s days <b>" % remaining.days)
    else:
        return ("Expiring in %s days" % remaining.days)

# function to add URL to a database


@eel.expose
def addURL(address):
    if validators.url(address):
        mycursor.execute(
            "INSERT or IGNORE INTO urls(url,expire,checked) VALUES ('%s','%s','%s')" % (address, "", ""))
        con.commit()
        checkURL(address)
        eel.setStatus("Inserted Url "+address)
    else:
        eel.setStatus("There is some error in your URL")

# Function to process data to put in table


@eel.expose
def loadURLs():
    sql = "select * from urls order by url"
    mycursor.execute(sql)
    resultData = mycursor.fetchall()
    tableData = []
    for row in resultData:
        tableRowList = []
        tableRowList.append(row[0])
        if(row[1] == ""):
            tableRowList.append("")
        else:
            ex = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            tableRowList.append(ssl_expires_in(ex))
        tableRowList.append(row[1])
        tableRowList.append(row[2])
        tableData.append(tableRowList)
    return tableData

# function to delete URL


@eel.expose
def deleteURL(address):
    mycursor.execute("DELETE FROM urls where url='%s'" % (address))
    con.commit()


# start desktop app
eel.start('index.html', size=(700, 700), close_callback=close_callback, port=0)

'''
Add verbose option
Everyone with {x} firstname or {x} lastname (column for first name and another for last name??)
return everyone with the same name
error check the input (have everything lowercase, or everything uppercase)
create a folder for the databases
if more than one database exsist then output menu to ask the user which one to connect to
'''

from subprocess import Popen, PIPE, check_output, CalledProcessError
import argparse
import sys
import time
import re
import os
import sqlite3 as lite
from threading import Thread, Event
import glob


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--domain',help='Gathers domain users',action='store_true',default=False)
    parser.add_argument('-u','--username',help='Look up full name based on username')
    parser.add_argument('-g','--group',help='View the groups a user is in', action='store_true')
    parser.add_argument('-fN','--full-name',help='Look up a username based on full name(ex. -fN "Firstname Lastname")')
    parser.add_argument('-p','--printDB',help='Prints the database',action='store_true')
    ##Take the len of the userList and find the position of the current user the programs if working on and calculate percentatge
    ##Speed up by threading
    return parser.parse_args()

def cmd(command):
    stdout, stderr = Popen(command.split(), stdout=PIPE, stderr=PIPE).communicate()
    return stdout

def connectDB(db):
    global con
    global cur
    con = lite.connect(db)
    cur = con.cursor()

def getDomain():
    domainName = cmd("wmic computersystem get domain")
    domainName = domainName.strip().split()[1]
    return domainName.decode('utf-8')

def getCompName():
    compName = cmd("wmic computersystem get name")
    compName = compName.strip().split()[1]
    return compName.decode('utf-8')

def get_allUsers(domain):
    if domain:
        users = cmd('net user /DOMAIN')
        users = users.decode('utf-8')
        pattern = re.compile("-")
        L = users.split('\n');del L[0:6]
        users = []
        for x in L:
            for user in x.split():
                users.append(user)
        return users
    else:
        users = cmd('net user')
        users = users.decode('utf-8')
        pattern = re.compile("-")
        L = users.split();del L[0:5];del L[-4:]
        return L

def create_userInfo(domain):

    start_time = time.time()

    ##Double check for a domain
    if getDomain() == "WORKGROUP":
        domain = False
    else:
        pass

    L = get_allUsers(domain)
    with open('userInfo.txt','w') as f:
        for user in L:
            if domain:
                ##Thread this maybe
                info = cmd('net user /DOMAIN {}'.format(user))
                pass
            else:
                info = cmd('net user {}'.format(user))
                pass

            info = info.decode('utf-8','ignore')

            username = info.split('\n')[2]
            if username.startswith("User name"):
                username = username.split()[2]
            else:
                continue


            fullName = info.split('\n')[3]
            try:
                fullName = fullName.split()[2:]
            except:
                fullName = 'NULL'

            fullName = ' '.join(map(str,fullName))

            cur.execute('INSERT INTO main VALUES(?,?)',(username,fullName))
            con.commit()

            f.write(info)
        f.close()
    con.close()

    elapsed_time = time.time() - start_time
    elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    print("[+]Time Elapsed: ", elapsed_time)

def get_userName(fullName):
    first = args.full_name.split(' ')[0]
    try:
        last = args.full_name.split(' ')[1]
        lastFirst = last +', '+ first
    except:
        last = None
        lastFirst = None

    cur.execute('SELECT * FROM main WHERE fullname=?', (fullName,))
    userName = cur.fetchone()

    if userName == None:
        cur.execute('SELECT * FROM main WHERE fullname=?', (lastFirst,))
        userName = cur.fetchone()
        if userName == None:
            print('[!]Error User not found')
            con.close()
    if userName != None:
        print("[+]User name for {} is: {}".format(fullName, userName[0]))
        con.close()

def get_fullName(userName):
    cur.execute('SELECT * FROM main WHERE username=?', (userName,))
    fullName = cur.fetchone()
    try:
        print("[+]Full name for {} is: {}".format(userName, fullName[1]))
    except:
        print('[!]Error User not found')
    finally:
        con.close()

def cleanup():
    ##Needs work
    print("[+]Cleaning up files that the script created")
    os.remove('userInfo.txt')
    sys.exit()

def print_DB():
    cur.execute('SELECT * from main')
    rows = cur.fetchall()

    for row in rows:
        print(row)

    con.close()

def get_Group(user):
    print("Getting group for {}".format(user))
    group = cmd("net user /domain {} | findstr 'Group'")
    print(group)

def firstRun(domain):
        print("[+]First Time running, please wait while the database is being created....")
        print("[*]This could take a long time...")

        if args.domain:
            domainName = getDomain()
            connectDB(domainName+"Users.db")
        else:
            compName = getCompName()

            connectDB(compName+"Users.db")

        cur.execute('CREATE TABLE main (username TEXT, fullname TEXT)')
        create_userInfo(args.domain)
        print("[+]Database has been created")
        print("[+]Please run 'userEnum.py -h' for options")
        sys.exit()

def main(args):
    domainName = getDomain()
    compName = getCompName()

    if not os.path.exists('UserInfo.txt'):
        firstRun(args.domain)

    if args.domain:
        #connectDB(domainName+"Users.db")
        connectDB("admin.rose.cc.ok.usUsers.db")
    else:
        connectDB(compName+"Users.db")

    if args.username:
        get_fullName(args.username)
    if args.full_name:
        get_userName(args.full_name)
    if args.cleanup:
        cleanup()
    if args.printDB:
        print_DB()
    if args.username and args.group:
        get_Group(args.username)

    con.close()

if __name__=='__main__':
    args = parse_args()
    main(args)

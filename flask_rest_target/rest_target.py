#!/usr/bin/env python
#
# Rest Target for Peach Class
#
# Copyright (c) Peach Fuzzer, LLC
#

from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from werkzeug.exceptions import HTTPException
import sqlite3, logging, logging.handlers, random

logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

@app.route("/")
def Home():
    with open('rest_target.html', 'r') as myfile:
        data=myfile.read()
    
    return data, 200, {'Content-Type':'text/html'}

@app.route("/api/.htaccess")
def FakeHtAccess():
    data = "look out, it's and .htaccess file!"
    return data, 200, {'Content-Type':'text/html'}

class ApiRoot(Resource):
    def get(self):
        return [
            '/api/users'
        ]

class ApiUsers(Resource):
    
    def validateToken(self):
        try:
            #logger.info("X-API-Key: %s", request.headers.get('X-API-Key'))
            if request.headers.get('X-API-Key') == "b5638ae7-6e77-4585-b035-7d9de2e3f6b3":
                return True
        except:
            pass
        
        return False
    
    def get(self):
        # Comment out auth check to trigger chail failure
        #if not self.validateToken():
        #    abort(401)
        
        logger.info("Getting all users")
        
        conn = GetConnection()
        users = []
        try:
            c = conn.cursor()
            for row in c.execute("select user_id, user, first, last, password from users"):
                user = {
                    "user_id" : row[0],
                    "user" : row[1],
                    "first" : row[2],
                    "last" : row[3],
                    "password" : row[4],
                }
                
                users.append(user)
                
        except HTTPException, e:
            raise e
        except Exception, e:
            logger.error('Error getting users: ' + str(e))
            abort(500)
        finally:
            conn.close()
        
        # Trigger sensitive information disclosure checks
        if random.randint(0,10) == 1:
            flip = random.randint(0,1)
            if flip == 0:
                return "Blah blah blah. Powered by: ASPX.NET Other other other", 200, {'Content-Type':'text/html'}
            elif flip == 1:
                return "Blah blah blah. Version: 1.1.1 Other other other", 200, {'Content-Type':'text/html'}
            
            return "Blah blah blah Stack trace: xxxxxx Ohter other other", 200, {'Content-Type':'text/html'}
        
        return users
        
    def post(self):
        if not self.validateToken():
            abort(401)
        
        json = request.get_json(force=True)
        
        logger.info("Creating new user '%s'"%json["user"])
        
        #for x in ['user', 'first', 'last', 'password']:
        #    if json[x] == "'":
        #        logger.info("SQL INJECTION ATTACK ON USER: %s" % json[x] )
        
        user_id = -1
        conn = GetConnection()
        try:
            c = conn.cursor()
            c.execute("insert into users (user, first, last, password) values ('%s', '%s', '%s', '%s')" % (
                json['user'], json['first'], json['last'], json['password'] ))
            user_id = c.lastrowid
            conn.commit()
            
            return {'user_id': user_id}, 201
        
        except HTTPException, e:
            raise e
        except Exception, e:
            logger.error('Error creating user: ' + str(e))
            abort(500)
        finally:
            conn.close()
    
    def delete(self):
        if not self.validateToken():
            abort(401)
        
        
        user = request.args.get('user')
        
        logging.info("Deleting user %s" % user)
        
        conn = GetConnection()
        try:
            c = conn.cursor()
            c.execute("delete from users where user = '%s'" % user)
            
            if c.rowcount == 0:
                abort(404, message = "User not found.")
            
            conn.commit()
            
            return {'user': user}, 204
        
        except HTTPException, e:
            raise e
        except Exception, e:
            logger.error('Error deleting user: %s' % (user, str(e)))
            abort(500, message="Error deleteing user")
        finally:
            conn.close

class ApiUser(Resource):
    def validateToken(self):
        try:
            #logger.info("X-API-Key: %s", request.headers.get('X-API-Key'))
            if request.headers.get('X-API-Key') == "b5638ae7-6e77-4585-b035-7d9de2e3f6b3":
                return True
        except Exception, e:
            logger.info("Failed to get X-API-Key from request: %s" % e)
            pass
        
        return False
    
    def get(self, user_id):
        if not self.validateToken():
            abort(401)
        
        logging.info("Getting user %d" % user_id)
        
        conn = GetConnection()
        try:
            c = conn.cursor()
            for row in c.execute("select user_id, user, first, last, password from users where user_id = %d" % user_id):
                
                return {
                    "user_id" : row[0],
                    "user" : row[1],
                    "first" : row[2],
                    "last" : row[3],
                    "password" : row[4],
                    "html" : "<b>"+row[3]+"</b>",
                }
            
            if c.rowcount == 0:
                abort(404, message = "User not found.")
            
        except HTTPException, e:
            raise e
        except Exception, e:
            logger.error('Error getting user_id %d: %s' % (user_id, str(e)))
            abort(500)
        finally:
            conn.close()
    
    def put(self, user_id):
        if not self.validateToken():
            abort(401)
        
        json = request.get_json(force=True)
        
        logger.info("Updating user_id %d"%user_id)
        
        conn = GetConnection()
        try:
            c = conn.cursor()
            c.execute("update users set user = '%s', first = '%s', last = '%s', password = '%s' where user_id = %d" % (
                json['user'], json['first'], json['last'], json['password'], user_id ))
            
            if c.rowcount == 0:
                logger.warning("User id not found while updating %d" % user_id)
                abort(404, message = "User not found.")
            
            conn.commit()
            
            return {'user_id': user_id}, 204
        
        except HTTPException, e:
            raise e
        except Exception, e:
            logger.error('Error creating user: ' + str(e))
            abort(500)
        finally:
            conn.close()
    
    def delete(self, user_id):
        if not self.validateToken():
            abort(401)
        
        logging.info("Deleting user %d" % user_id)
        
        conn = GetConnection()
        try:
            c = conn.cursor()
            c.execute("delete from users where user_id = %d" % user_id)
            
            if c.rowcount == 0:
                abort(404, message = "User not found.")
            
            conn.commit()
            
            return {'user_id': user_id}, 204
        
        except HTTPException, e:
            raise e
        except Exception, e:
            logger.error('Error deleting user_id: %s' % (user_id, str(e)))
            abort(500, message="Error deleteing user")
        finally:
            conn.close

api.add_resource(ApiRoot,  '/api')
api.add_resource(ApiUsers, '/api/users')
api.add_resource(ApiUser,  '/api/users/<int:user_id>')

def GetConnection():
    return sqlite3.connect("rest_target.db")

def CreateDb():
    logger.info("Creating in-memory database.")
    conn = GetConnection()
    try:
        c = conn.cursor()
        c.execute('drop table if exists users')
        c.execute('''create table users (user_id integer primary key, user text unique, first text, last text, password text)''')
        c.execute('''insert into users (user, first, last, password) values ('admin', 'Joe', 'Smith', 'Password!')''')

        user_id = str(c.lastrowid)

        c.execute('drop table if exists msgs')
        c.execute('''create table msgs (msg_id integer primary key, from_id int, to_id int, subject text, msg text)''')
        c.execute('''insert into msgs (from_id, to_id, subject, msg) values ('''+user_id+''','''+user_id+''', 'Hello From Myself', 'Welcome to the system...!')''')
        conn.commit()
    except Exception, e:
        logger.error('Error creating user: ' + str(e))
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
    syslogHandler = logging.handlers.SysLogHandler()
    syslogHandler.setFormatter(logFormatter)
    logger.addHandler(syslogHandler)
    
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    
    fileHandler = logging.FileHandler('rest_target.log')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    logger.info("rest_target.py initializing.")
    CreateDb()
    logger.info("Starting REST application")
    app.run(debug=True, host="0.0.0.0", port=7777)

# end

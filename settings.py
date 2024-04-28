import time
import json
import libsql_experimental as libsql
import creds

conn = libsql.connect(database=creds.LIBSQL_URL,
                      auth_token=creds.LIBSQL_TOKEN)

def reconnect():
   global conn
   conn = libsql.connect(database=creds.LIBSQL_URL,
                      auth_token=creds.LIBSQL_TOKEN)

notcorrect = conn.execute("select * from mapping").fetchall()

tunnels = []

for i in notcorrect:
   tunnels.append({"name":i[0],"host":i[1],"target":i[2]})

def refresh_tunnels():
   notcorrect = conn.execute("select * from mapping").fetchall()
   global tunnels
   tunnels = []
   for i in notcorrect:
      tunnels.append({"name":i[0],"host":i[1],"target":i[2]})
      conn.execute("END TRANSACTION;")
def add_tunnels(name,host,target):
   tunnels.append({"name":name,"host":host,"target":target, "edited": True})
   save()

def save():
   conn.execute("END TRANSACTION;")
   i1 = 0
   for i in tunnels:
     if not i.get("edited"):
       pass
     conn.execute("END TRANSACTION;")
     if not i.get("editname"):
        conn.execute("INSERT OR REPLACE INTO mapping (name, host, target) VALUES ('" + i["name"] + "','" + i["host"] + "','" + i["target"] + "');")
     else:
        conn.execute("DELETE FROM mapping WHERE name='" + i["name"] + "';")
        time.sleep(1)
        conn.execute("END TRANSACTION;")
        conn.execute("INSERT INTO mapping (name, host, target) VALUES ('" + i["editname"] + "','" + i["host"] + "','" + i["target"] + "');")
        
     i1 = i1 + 1
   conn.commit()
   conn.execute("END TRANSACTION;")
   

def delete_tunnels(name):
  itr = 0
  for i in tunnels:
     if i["name"] == name:
       conn.execute("END TRANSACTION;")
       tunnels.pop(itr)
       conn.execute("DELETE FROM mapping WHERE name='" + name + "';")
       conn.commit()
       return "ok"
     else:
       itr = itr + 1
  return "nook"

def get_settings():
   notcorrect = conn.execute("select * from settings").fetchall()
   temp = {}
   for i in notcorrect:
      temp[i[0]] = i[1]
   return temp

def get_auth_control():
   notcorrect = conn.execute("select * from auth_control").fetchall()
   temp = {}
   for i in notcorrect:
      temp[i[0]] = i[1]
   conn.execute("END TRANSACTION;")
   return temp


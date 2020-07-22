# coding:utf-8

from flask import Flask, render_template, request, g
from flask_socketio import SocketIO
# from PIL import Image as im
# from io import BytesIO as bio
# from skimage.filters import sobel

import traceback
import json
import base64
import decimal
import logging
import threading
import time
import zmq
import random
import os
import numpy as np
# import gen_hd_global_map_tool
# from constants import CONFIG_PATH, IMG_LENGTH
# from utils import get_db_path
# import sqlite3
import struct
import socket


log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nuaacmee'
sio = SocketIO(app)

def tojson(obj):
  return json.dumps(obj).encode('utf-8')

def get_socket():
  s = getattr(g, '_socket_tcp', None)
  if s is None:
    g._socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  g._socket_tcp.connect(('192.168.1.100', 10086))
  s = g._socket_tcp
  return s

class FetchRegLoop(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.running = False
    self.aliving = False
    self.hz = 0.1

    def run(self):
      with app.app_context():
        flist = []
        for _,_,fs in os.walk('static/img'):
          for f in fs:
            flist.append(f)
            break
          while True:
            try:
              if not self.aliving:
                print('hanging thread by running flag...')
                break
              if not self.running:
                time.sleep(self.hz)
                print('terminating thread by running flag...')
                continue
              sio.emit('json', json_data)
              time.sleep(self.hz)
            except Exception as e:
              traceback.print_exc()
              # pass

loop = FetchRegLoop()

@app.route('/')
def index():
  return render_template('index.html')


@app.route('/api/restart_daemon_process', methods=['GET'])
def restart_daemon_process():
  global loop
  try:
    if loop.aliving:
      loop.aliving = False
      del loop
      loop = FetchRegLoop()
      loop.running = True
      loop.aliving = True
      loop.daemon = True
      loop.start()
    else:
      loop.running = True
      loop.aliving = True
      loop.daemon = True
      loop.start()
      return tojson({'message':'start threading'})
  except Exception as e:
    traceback.print_exc()
  finally:
    return tojson({'message':'restart daemon process finished'})

@app.route('/api/setio/<x>', methods=['GET'])
def setio(x):
  global loop
  # print("set io No.%s" % x)
  data = bytes()
  data += struct.pack("<B", 0xAA)
  data += struct.pack("<B", 0x10)
  data += struct.pack("<B", int(x))
  get_socket().send(data)
  print(data)
  return tojson({'message':'success'})

@app.route('/api/unsetio/<x>', methods=['GET'])
def unsetio(x):
  global loop
  # print("set io No.%s" % x)
  data = bytes()
  data += struct.pack("<B", 0xAA)
  data += struct.pack("<B", 0x12)
  data += struct.pack("<B", int(x))
  get_socket().send(data)
  print(data)
  return tojson({'message':'success'})

@app.teardown_appcontext
def close_connect(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

@sio.on('connect establish event')
def handle_connect_establish_socket(msg):
  print('connection established with message : "%s"' % msg)

class MyEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, bytes):
      return str(obj, encoding='utf-8');
    return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
  sio.run(app, host='0.0.0.0', port=5000, debug=True)

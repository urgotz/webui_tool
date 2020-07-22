# coding:utf-8

import traceback
import sqlite3
import os
import shutil
import time
import numpy as np
from datetime import datetime

from PIL import Image as im
from PIL import ImageQt as imq

from PyQt5.QtGui import QImage

from constants import DEFAULT_DB_PATH
from constants import CONFIG_PATH, IMG_LENGTH

#M2PRATIO = 0.40625
M2PRATIO = 0.359 * 2
PIXROTATE = 90
XGAP = 1000.0
YGAP = 1000.0
g_maxx = 0
g_maxy = 0
g_minx = 1e10
g_miny = 1e10
g_db_path = None


class Frame:
    def __init__(self, img, idx, x, y, t):
        self.img = img
        self.idx = idx
        self.ox = x
        self.oy = y
        self.ot = t


def get_db_path():
    global g_db_path
    if False:
        return
    else:
        g_db_path = DEFAULT_DB_PATH
        if os.path.exists(CONFIG_PATH):
            lines = open(CONFIG_PATH).readlines()
            for line in lines:
                if "texture_map=" in line:
                    line = line.strip('\n')
                    g_db_path = line.split('=')[1]
                    break

def empty_dir(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path, True)
            os.makedirs(path)
        else:
            os.makedirs(path)
        return True
    except Exception as e:
        traceback.print_exc()
        return False
    
def check_db_not_empty():
    global g_db_path
    conn = None
    curs = None
    try:
        conn = sqlite3.connect(g_db_path)
        curs = conn.cursor()
        # time_start = datetime.now()
        res = curs.execute('select id from zhdl_map limit 1')
        conn.commit()
        # time_end = datetime.now()
        # print('load_data_from_db() cost', time_end-time_start)
        cnt = len(list(res))
        # print("cnt:",cnt)
        if cnt == 0:
            print("No data in database")
            return False
        else:
            return True
    except Exception as e:
        traceback.print_exc()
        return False
    finally:
        if curs:
            curs.close()
        if conn:
            conn.close()

def load_id_pos_from_db(x=2000, y=2000, half_width=2000, use_all_data=True):
    global g_maxx, g_maxy, g_minx, g_miny, g_db_path
    g_maxx = 0
    g_maxy = 0
    g_minx = 1e10
    g_miny = 1e10

    # time_start = datetime.now()
    all_id_kp_list = []
    key_point_id_kp_tmp_list = []
    conn = None
    curs = None
    try:
        conn = sqlite3.connect(g_db_path)
        curs = conn.cursor()
        where_str = "" if use_all_data else " where x>={} and x<{} and y>={} and y<{}".format(x-half_width, x+half_width, y-half_width, y+half_width)
        res = curs.execute('select id, x, y, is_keypoint from zhdl_map' + where_str)

        for data in res:
            try:
                idx = data[0]
                x = data[1]
                y = -1 * data[2]
                kp = data[3]    # KeyPoints should be shown in the front
                g_maxx = max(x, g_maxx)
                g_maxy = max(abs(y), g_maxy)
                g_minx = min(x, g_minx)
                g_miny = min(abs(y), g_miny)

                if kp == 1:
                    key_point_id_kp_tmp_list.append(idx)
                else:
                    all_id_kp_list.append(idx)
            except Exception as e:
                traceback.print_exc()
                break
        # key points order in the back, so that they get dipicted in the front.
        all_id_kp_list.extend(key_point_id_kp_tmp_list)
        print("map total size is:", len(all_id_kp_list), ", key_point type size is:", len(key_point_id_kp_tmp_list))
        
        return all_id_kp_list
    except Exception as e:
        traceback.print_exc()
    finally:
        if curs:
            curs.close()
        if conn:
            conn.close()
        # time_end = datetime.now()
        # print('load_id_pos_from_db() cost', time_end-time_start)

def load_data_from_db_by_ids(ids):
    global g_db_path
    # time_start = datetime.now()
    all_pics_list = []
    conn = None
    curs = None
    try:
        conn = sqlite3.connect(g_db_path)
        curs = conn.cursor()

        ids_str = ','.join(str(id) for id in ids)
        # print("ids_str:", ids_str)
        res = curs.execute('select id, x, y, heading, raw_image, is_keypoint, fixed from zhdl_map where id in ({})'.format(ids_str))
        tmp_dict = {}
        for data in res:
            try:
                idx = data[0]
                x = data[1]
                y = -1 * data[2]
                t = data[3]
                kp = data[5]    # KeyPoints should be shown in the front
                fixed = data[6]
                qImage = QImage(data[4], IMG_LENGTH, IMG_LENGTH, QImage.Format_Grayscale8)
                frame = Frame(qImage, idx, x, y, t)
                tmp_dict[idx] = frame
                
            except Exception as e:
                traceback.print_exc()
                break
        # ensure the order
        for idx in ids:
            all_pics_list.append(tmp_dict[idx])
        return all_pics_list
    except Exception as e:
        traceback.print_exc()
    finally:
        if curs:
            curs.close()
        if conn:
            conn.close()
        # time_end = datetime.now()
        # print('load_data_from_db_by_ids() cost', time_end-time_start)


def gen_hd_global_map_img(x=2000, y=2000, half_width=2020, use_all_data=True):
    global g_maxx, g_maxy, g_minx, g_miny, g_db_path
    get_db_path()
    print('g_db_path is:' + g_db_path)
    if not check_db_not_empty():
        return
    ids = load_id_pos_from_db(x, y, half_width, use_all_data)
    if not ids:
        return
    
    time_start = datetime.now()
    width_max = 10240
    height_max = 10240
    canvas_width_param = g_maxx - g_minx + 2000
    canvas_height_param = g_maxy - g_miny + 2000
    if canvas_width_param > canvas_height_param:
        gv_width = width_max
        zoom_scale = float(width_max) / canvas_width_param
        gv_height = int(width_max * canvas_height_param / canvas_width_param)
    else:
        gv_height = height_max
        zoom_scale = float(height_max) / canvas_height_param
        gv_width = int(height_max * canvas_width_param / canvas_height_param)
    img_scale = max(int(IMG_LENGTH * zoom_scale * M2PRATIO), 1)
    gv_canvas = im.new('L', (gv_width, gv_height))
    
    MAX_BATCH_SIZE=10000
    batch_list = [ids[i:i+MAX_BATCH_SIZE] for i in range(0, len(ids), MAX_BATCH_SIZE)]
    i=0
    for batch_ids in batch_list:
        i = i + 1
        print("processing {}th batch data, batch size:{}".format(i, len(batch_ids)))
        
        all_pics_list = load_data_from_db_by_ids(batch_ids)
        #time_start1 = datetime.now()
        for itm in all_pics_list:
            img = imq.fromqpixmap(itm.img).convert('L').resize((img_scale, img_scale))
            rot = itm.ot - PIXROTATE
            arr = np.array(img.convert('RGBA'))
            arr[:, :, 3] = (arr[:, :, 0] + arr[:, :, 1] + arr[:, :, 2] != 0) * arr[:, :, 3]
            gmi = im.fromarray(arr.astype('uint8')).rotate(rot, expand=True)
            shift = (gmi.size[0] - img_scale) // 2
            pos_x = int(gv_width * ((itm.ox - shift) - g_minx + XGAP) / canvas_width_param)
            pos_y = int(gv_height * ((-1 * itm.oy + shift) - g_miny + YGAP) / canvas_height_param)
            gv_canvas.paste(gmi, (pos_x - img_scale // 2, gv_height - (pos_y - img_scale // 2)), gmi)
        # time_end1 = datetime.now()
        # print('paste pictures cost', time_end1-time_start1)
    dir_path = os.path.dirname(os.path.realpath(__file__)) + '/static/maps/'
    
    empty_dir(dir_path)
    time_str = time.strftime("%Y-%m-%d_%H-%M-%S",time.localtime(time.time()))
    pic_file_name = "hd_global_viewmap" + time_str + '.png'
    pic_path = dir_path + pic_file_name

    gv_canvas.save(pic_path)
    time_end = datetime.now()
    print('gen_hd_global_map_img() cost', time_end-time_start)
    relative_pic_path = 'static/maps/' + pic_file_name
    return relative_pic_path # for show

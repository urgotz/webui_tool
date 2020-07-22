import os
from constants import DEFAULT_DB_PATH, CONFIG_PATH
g_db_path = None

def get_db_path():
    global g_db_path
    if g_db_path is None:
        print("enter here")
        g_db_path = DEFAULT_DB_PATH
        if os.path.exists(CONFIG_PATH):
            lines = open(CONFIG_PATH).readlines()
            for line in lines:
                if "texture_map=" in line:
                    line = line.strip('\n')
                    g_db_path = line.split('=')[1]
                    break
    return g_db_path
import json
import os
import pandas as pd
import numpy as np

from starrynet.sn_observer import *
from starrynet.sn_orchestrater import *
from starrynet.sn_synchronizer import *

def load_config(conf_path):
    with open(conf_path, 'r') as conf_file:
        return json.load(conf_file)
    
    
if __name__ == '__main__':
    # first GW then Cells
    AS = [[1, 136]]
    gw_indices = [x for x in range(101, 105)]
    cell_indices = [x for x in range(105, 137)]
    
    with open ('sim_configs/GW_location.txt', 'r') as gw_file:
        GW_lat_long = [list(map(float, line.strip().replace('[', '').replace(']', '').split(','))) for line in gw_file.readlines()]
    with open ('sim_configs/UE_location.txt', 'r') as ue_file:
        UE_lat_long = [list(map(float, line.strip().replace('[', '').replace(']', '').split(','))) for line in ue_file.readlines()]
    
    all_lat_long = GW_lat_long + UE_lat_long
    
    GW_conf_file_path = './gs_config.json'
    
    hello_interval = 1
    
    print('Start StarryNet.')
    sn = StarryNet(GW_conf_file_path, all_lat_long, hello_interval, AS)
    sn.create_nodes()
    sn.create_links()
    sn.run_routing_deamon()
   
    # with open('logs/neighbors.txt', 'w') as neighbors_file:
    #     for node_idx in range(1, 137):
    #         for time_idx in range(2, 60, 1):
    #             neighbors = sn.get_neighbors(node_idx, time_idx)
    #             log_entry = '{}|{}|{}\n'.format(node_idx, time_idx, str(neighbors))
    #             
    #             neighbors_file.write(log_entry)
    
    # with open('logs/conn_GW_cells.txt', 'w') as GWC_file:
    #     for node_idx in range(1, 101):
    #         for time_idx in range(2, 60, 1):
    #             GWC = sn.get_GSes(node_idx, time_idx)
    #             log_entry = '{}|{}|{}\n'.format(node_idx, time_idx, str(GWC))
    #             
    #             GWC_file.write(log_entry)
     
    # for t in range(12, 25):
    #     sn.set_ping(111, 104, t)
        
    for t in range(2, 25, 5):
        sn.set_perf(111, 104, t, 100)
        
    for t in range(2, 25, 5):
        sn.set_perf(101, 109, t, 100)
    
    # # load cell/GW assignments
    # assignments_df = pd.read_csv('sim_configs/assignment.csv').to_numpy()
    # assignments_time = assignments_df[:, 0], assignments = assignments_df[:, 1:]
    
    # # load cell_demand
    # demands_df = pd.read_csv('sim_configs/user_demand.csv').to_numpy()
    # demands_time = demands_df[:, 0], demands = demands_df[:, 1:]
    
    # for idx, time in enumerate(demands_time):
    #     for 
    #     sn.set_perf()
    sn.start_emulation()
    sn.stop_emulation()
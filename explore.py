import json
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from starrynet.sn_observer import *
from starrynet.sn_orchestrater import *
from starrynet.sn_synchronizer import *

def load_config(conf_path):
    with open(conf_path, 'r') as conf_file:
        return json.load(conf_file)
    
    
if __name__ == '__main__':
    # first GW then Cells
    constellation_conf_dir = './sim_configs/small_2/'
    
    satellites_num = 61
    AS = [[1, satellites_num + 3 + 147]]
    gw_indices = [x for x in range(satellites_num + 1, satellites_num + 4)]
    cell_indices = [x for x in range(satellites_num + 4, satellites_num + 151)]
    
    handover_type = 'CU-1'

    # load ground stations latitudes and longitudes
    gw_df = pd.read_csv(constellation_conf_dir + 'gw.csv')
    GW_lat_long = [[float(gw_df['latitude'][i]), float(gw_df['longitude'][i])] for i in range(gw_df.shape[0])]
    ue_df = pd.read_csv(constellation_conf_dir + 'users.csv')
    UE_lat_long = [[float(ue_df['lat'][i]), float(ue_df['lng'][i])] for i in range(ue_df.shape[0])]
    # with open ('sim_configs/GW_location.txt', 'r') as gw_file:
    #     GW_lat_long = [list(map(float, line.strip().replace('[', '').replace(']', '').split(','))) for line in gw_file.readlines()]
    # with open ('sim_configs/UE_location.txt', 'r') as ue_file:
    #     UE_lat_long = [list(map(float, line.strip().replace('[', '').replace(']', '').split(','))) for line in ue_file.readlines()]

    all_lat_long = GW_lat_long + UE_lat_long
    
    GW_conf_file_path = './gs_config.json'
    
    hello_interval = 1
    
    # slow assignments configuration
    # assignments_df = np.genfromtxt('./sim_configs/assignment.csv', delimiter=',', skip_header=1)
    # assignments_time = assignments_df[:, 0]
    assignments = np.genfromtxt('./sim_configs/small_2/cell_assignment.csv', delimiter=',', dtype=int)
    
    # user demands
    # demands_df = np.genfromtxt('./sim_configs/user_demand.csv', delimiter=',', skip_header=1)
    # demands_time = demands_df[:, 0]
    demands = np.ones((assignments.shape[0]))*600 # Mbps
    
    print('Start StarryNet.')
    sn = StarryNet(constellation_conf_dir, GW_conf_file_path, all_lat_long, 
                   handover_type, assignments, demands, satellites_num, 
                   hello_interval, AS, gw_indices, cell_indices)
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
     
    # for t_idx, t in enumerate(assignments_time):
    #     for cell_idx, cell in enumerate(cell_indices):
    #         sn.set_ping(cell, gw_indices[assignments[t_idx, cell_idx]], t)
    #         # sn.set_traceroute(cell, gw_indices[assignments[t_idx, cell_idx]], t)
    
    # for t_idx, t in enumerate(assignments_time):
    #     sn.set_ping(cell_indices[0], gw_indices[assignments[t_idx, 0]], t)
    
    # for t_idx, t in enumerate(assignments_time):
    #     sn.set_perf(cell_indices[1], gw_indices[assignments[t_idx, 1]], 
    #                 t, demands[t_idx, 1])
    
    # for t in range(12, 25):
    #     sn.set_ping(111, 104, t)
        
    # for t in range(2, 25, 5):
    #     sn.set_perf(111, 104, t, 100)
        
    sn.start_emulation()
    sn.stop_emulation()
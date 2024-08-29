import json

from starrynet.sn_observer import *
from starrynet.sn_orchestrater import *
from starrynet.sn_synchronizer import *

def load_config(conf_path):
   with open(conf_path, 'r') as conf_file:
      return json.load(conf_file)

if __name__ == "__main__":

   # The node index sequence is: 25 sattelites, 5 ground stations.
   # In this example, 25 satellites and 2 ground stations are one AS.

   AS = [[1, 137]]  # Node #1 to Node #27 are within the same AS.
   with open('GW_location.txt') as gs_file:
      GS_lat_long = [list(map(float, line.strip().replace('[', '').replace(']', '').split(','))) for line in gs_file.readlines()]
   with open('UE_location.txt') as ue_file:
      UE_lat_long = [list(map(float, line.strip().replace('[', '').replace(']', '').split(','))) for line in ue_file.readlines()]
      
   all_lat_long = GS_lat_long + UE_lat_long
   
   GS_conf_file_path = './gs_config.json'
   UE_conf_file_path = './ue_config.json'

   hello_interval = 1  # hello_interval(s) in OSPF. 1-200 are supported.

   print('Start StarryNet.')
   sn = StarryNet(GS_conf_file_path, all_lat_long, hello_interval, AS)
   sn.create_nodes()
   sn.create_links()
   sn.run_routing_deamon()
   
   # Initialize variables to store closest pairs and their distances
   closest_pairs = {}  # <-- Initialize closest_pairs dictionary
   closest_distances = {}
   
   time_index = 2
   HO = 0
   
   with open("logfile.txt","w") as logfile:
     for node_index in range(101,106):
      for time_index in range (2,5400,60):
        neighbors_index = sn.get_neighbors(node_index, time_index)
        for neighbor_index in neighbors_index: # Iterate over each neighbor
           LLA = sn.get_position(neighbor_index, time_index) # Corrected to use neighbor_index
           log_entry = "{}.{}.{}.{}\n".format(neighbors_index, time_index, node_index,str(LLA))
            #node.time.GS.position
           logfile.write(log_entry)

     #Assume there is a change in GSL BW if there is a HO
        with open('config.json', 'r') as f:
         config_data = json.load(f)
   
         if time_index > 2:
          time_index_1 = time_index - 2
          neighbors_index_1 = sn.get_neighbors(node_index, time_index_1)
          if neighbors_index_1 != neighbors_index: 
             HO = HO + 1
             
             #Update the "sat-ground bandwidth (\"X\" gbit)" value to be 1 less than the current value
             current_sat_ground_bandwidth = config_data["sat-ground bandwidth (\"X\" gbit)"]
             new_sat_ground_bandwidth = current_sat_ground_bandwidth - 1
             #config_data["satellite link bandwidth (\"X\" gbit)"] = 5
             config_data["sat-ground bandwidth (\"X\" gbit)"] = new_sat_ground_bandwidth

             # Write the updated data back to the JSON file
             with open('config.json', 'w') as f:
              json.dump(config_data, f, indent=4)
     print("Handover is {}",format(HO))
   

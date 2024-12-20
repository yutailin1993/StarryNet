#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
StarryNet: empowering researchers to evaluate futuristic integrated space and terrestrial networks.
author: Zeqi Lai (zeqilai@tsinghua.edu.cn) and Yangtao Deng (dengyt21@mails.tsinghua.edu.cn)
"""
from starrynet.sn_observer import *
from starrynet.sn_utils import *


class StarryNet():

    def __init__(self,
                 constellation_conf_dir,
                 configuration_file_path,
                 GS_lat_long,
                 handover_type,
                 assigned_gw,
                 demands,
                 constellation_size,
                 hello_interval=10,
                 AS=[],
                 gw_list=[],
                 cell_list=[]):
        # Initialize constellation information.
        sn_args = sn_load_file(configuration_file_path, GS_lat_long)
        self.name = sn_args.cons_name
        self.satellite_altitude = sn_args.satellite_altitude
        self.inclination = sn_args.inclination
        self.orbit_number = sn_args.orbit_number
        self.sat_number = sn_args.sat_number
        self.fac_num = sn_args.fac_num
        self.constellation_size = constellation_size
        self.node_size = self.constellation_size + sn_args.ground_num
        self.link_style = sn_args.link_style
        self.IP_version = sn_args.IP_version
        self.link_policy = sn_args.link_policy
        self.update_interval = sn_args.update_interval
        self.duration = sn_args.duration
        self.inter_routing = sn_args.inter_routing
        self.intra_routing = sn_args.intra_routing
        self.cycle = sn_args.cycle
        self.time_slot = sn_args.time_slot
        self.sat_bandwidth = sn_args.sat_bandwidth
        self.sat_ground_bandwidth = sn_args.sat_ground_bandwidth
        self.sat_loss = sn_args.sat_loss
        self.sat_ground_loss = sn_args.sat_ground_loss
        self.ground_num = sn_args.ground_num
        self.multi_machine = sn_args.multi_machine
        self.gw_antenna_number = sn_args.gw_antenna_number
        self.cell_antenna_number  = sn_args.cell_antenna_number
        self.antenna_inclination = sn_args.antenna_inclination
        self.container_global_idx = 1
        self.plane_number = 2

        self.assigned_gw = assigned_gw
        self.demands = demands
        self.handover_type = handover_type
        self.hello_interval = hello_interval
        self.AS = AS
        self.gw_list = gw_list
        self.cell_list = cell_list
        self.configuration_file_path = os.path.dirname(
            os.path.abspath(configuration_file_path))
        self.file_path = './' + sn_args.cons_name + '-' + str(
            self.constellation_size) + '-' + str(self.ground_num) + '-' + str(
                sn_args.satellite_altitude) + '-' + str(
                    sn_args.inclination
                ) + '-' + sn_args.link_style + '-' + sn_args.link_policy
        self.constellation_conf_dir = os.path.abspath(constellation_conf_dir)
        self.observer = Observer(self.file_path, self.configuration_file_path,
                                 self.constellation_conf_dir,
                                 self.inclination, self.satellite_altitude,
                                 self.orbit_number, self.sat_number,
                                 self.duration, self.gw_antenna_number,
                                 self.cell_antenna_number, self.gw_list, 
                                 self.cell_list, GS_lat_long, 
                                 self.antenna_inclination,
                                 self.intra_routing, self.hello_interval,
                                 self.constellation_size, self.AS)
        self.docker_service_name = 'constellation-test'
        self.isl_idx = 0
        self.ISL_hub = 'ISL_hub'
        self.container_id_list = []
        self.n_container = 0
        # Get ssh handler.
        self.remote_ssh, self.transport = sn_init_remote_machine(
            sn_args.remote_machine_IP, sn_args.remote_machine_username,
            sn_args.remote_machine_password)
        if self.remote_ssh is None:
            print('Remote SSH login failure.')
            return
        if self.transport is None:
            print('Remote transport login failure.')
            return
        self.remote_ftp = sn_init_remote_ftp(self.transport)
        if self.remote_ftp is None:
            print('Remote ftp login failure.')
            return
        self.utility_checking_time = []
        self.ping_src = []
        self.ping_des = []
        self.ping_time = []
        self.handover_srcs = []
        self.handover_targets = []
        self.handover_times = []
        self.perf_src = []
        self.perf_des = []
        self.perf_time = []
        self.perf_throughputs = []
        self.sr_src = []
        self.sr_des = []
        self.sr_target = []
        self.sr_time = []
        self.damage_ratio = []
        self.damage_time = []
        self.damage_list = []
        self.recovery_time = []
        self.route_src = []
        self.route_time = []
        
        self.traceroute_src = []
        self.traceroute_dst = []
        self.traceroute_time = []

        # Initiate a working directory
        sn_thread = sn_init_directory_thread(self.file_path,
                                             self.configuration_file_path,
                                             self.remote_ssh)
        sn_thread.start()
        sn_thread.join()
        # Initiate a necessary delay and position data for emulation
        self.observer.calculate_delay()
        # Generate configuration file for routing
        self.observer.generate_conf(self.remote_ssh, self.remote_ftp)

    def create_nodes(self):
        # Initialize each machine in multiple threads.
        sn_thread = sn_Node_Init_Thread(self.remote_ssh,
                                        self.docker_service_name,
                                        self.node_size, self.container_id_list,
                                        self.container_global_idx)
        sn_thread.start()
        sn_thread.join()
        self.container_id_list = sn_get_container_info(self.remote_ssh)
        print("Constellation initialization done. " +
              str(len(self.container_id_list)) + " have been created.")

    def create_links(self):
        print("Create Links.")
        isl_thread = sn_Link_Init_Thread(
            self.remote_ssh, self.remote_ftp, self.orbit_number,
            self.sat_number, self.constellation_size, self.fac_num,
            self.file_path, self.configuration_file_path, self.sat_bandwidth,
            self.sat_ground_bandwidth, self.sat_loss, self.sat_ground_loss, 
            self.plane_number, self.constellation_conf_dir)
        isl_thread.start()
        isl_thread.join()
        # self._create_core_network()
        print("Link initialization done.")
        
    def _create_core_network(self):
        print ("Create Core Network.")
        # create links for Gateway to core network
        core_node = self.constellation_size + self.fac_num + 1 # core node ID (not idx)
        core_network = "CORE_NETWORK"
    
        os.system('docker network create ' + core_network +
                  ' --subnet 9.{}.{}.0/24'.format(core_node, core_node))
        print ("[Create core network:]" + "docker network create " + core_network + 
               " --subnet 9.{}.{}.0/24".format(core_node, core_node))
        os.system('docker network connect ' + core_network + ' ' + 
                  str(self.container_id_list[core_node - 1]) + ' --ip 9.' +
                  str(core_node) + '.' + str(core_node) + '.10')
    
        with os.popen(
            "docker exec -it " + str(self.container_id_list[core_node - 1]) +
            " ip addr | grep -B 2 9." + str(core_node) + "." + str(core_node) +
            ".10 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'"
        ) as f:
            ifconfig_output = f.readline()
            target_interface = str(ifconfig_output).split("@")[0]
            os.system('docker exec -d ' + str(self.container_id_list[core_node - 1]) +
                      ' ip link set dev ' + target_interface + ' down')
            os.system('docker exec -d ' + str(self.container_id_list[core_node - 1]) +
                      ' ip link set dev ' + target_interface + ' name ' + 'B' +
                      str(core_node) + '-core')
            os.system('docker exec -d ' + str(self.container_id_list[core_node - 1]) +
                      ' ip link set dev B' + str(core_node) + '-core up')
        print ("[Add core network node:] " + "docker network connect " + core_network +
                " " + str(self.container_id_list[core_node - 1]) + " --ip 9." + 
                str(core_node) + "." + str(core_node) + ".10")
        
        for j in range(self.constellation_size + 1, self.constellation_size + len(self.gw_list) + 1):
            os.system('docker network connect ' + core_network + ' ' +
                      str(self.container_id_list[j - 1]) + ' --ip 9.' + str(core_node) + '.' +
                      str(core_node) + '.' + str(j))
            with os.popen(
                'docker exec -it ' + str(self.container_id_list[j - 1]) +
                ' ip addr | grep -B 2 9.' + str(core_node) + '.' + str(core_node) +
                '.' + str(j) + " | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'"
            ) as f:
                ifconfig_output = f.readline()
                target_interface = str(ifconfig_output).split("@")[0]
                os.system('docker exec -d ' + str(self.container_id_list[j - 1]) +
                          ' ip link set dev ' + target_interface + ' down')
                os.system('docker exec -d ' + str(self.container_id_list[j - 1]) +
                          ' ip link set dev ' + target_interface + ' name ' + 'B' +
                          str(j) + '-core')
                os.system('docker exec -d ' + str(self.container_id_list[j - 1]) +
                          ' ip link set dev B' + str(j) + '-core up')
            print ("[Add current node to core:]" + "docker network connect " + core_network +
                   " " + str(self.container_id_list[j - 1]) + " --ip 9." + str(core_node) + "." +
                   str(core_node) + "." + str(j))

    def run_routing_deamon(self):
        routing_thread = sn_Routing_Init_Thread(
            self.remote_ssh, self.remote_ftp, self.orbit_number,
            self.sat_number, self.constellation_size, self.fac_num,
            self.file_path, self.sat_bandwidth, self.sat_ground_bandwidth,
            self.sat_loss, self.sat_ground_loss)
        routing_thread.start()
        routing_thread.join()
        print("Bird routing in all containers are running.")

    def get_distance(self, sat1_index, sat2_index, time_index):
        delaypath = self.configuration_file_path + "/" + self.file_path + '/delay/' + str(
            time_index) + '.txt'
        adjacency_matrix = sn_get_param(delaypath)
        delay = float(adjacency_matrix[sat1_index - 1][sat2_index - 1])
        dis = delay * (17.31 / 29.5 * 299792.458) / 1000  # km
        return dis

    def get_neighbors(self, sat_index, time_index):
        neighbors = []
        delaypath = self.configuration_file_path + "/" + self.file_path + '/delay/' + str(
            time_index) + '.txt'
        adjacency_matrix = sn_get_param(delaypath)
        sats = self.constellation_size
        for i in range(sats):
            if (float(adjacency_matrix[i][sat_index - 1]) > 0.01):
                neighbors.append(i + 1)
        return neighbors

    def get_GSes(self, sat_index, time_index):
        GSes = []
        delaypath = self.configuration_file_path + "/" + self.file_path + '/delay/' + str(
            time_index) + '.txt'
        adjacency_matrix = sn_get_param(delaypath)
        sats = self.constellation_size
        for i in range(sats, len(adjacency_matrix)):
            if (float(adjacency_matrix[i][sat_index - 1]) > 0.01):
                GSes.append(i + 1)
        return GSes

    def get_utility(self, time_index):
        self.utility_checking_time.append(time_index)

    def get_position(self, sat_index, time_index):
        path = self.configuration_file_path + "/" + self.file_path + '/position/' + '/%d.txt' % time_index
        f = open(path)
        ADJ = f.readlines()
        return ADJ[sat_index - 1]

    def get_IP(self, sat_index):
        IP_info = sn_remote_cmd(
            self.remote_ssh, "docker inspect" +
            " --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}\n{{end}}'"
            + " ovs_container_" + str(sat_index))
        ip_list = []
        for i in range(len(IP_info) - 2):
            ip_list.append(IP_info[i].split()[0])
        return ip_list

    def set_damage(self, damaging_ratio, time_index):
        self.damage_ratio.append(damaging_ratio)
        self.damage_time.append(time_index)

    def set_recovery(self, time_index):
        self.recovery_time.append(time_index)

    def check_routing_table(self, sat_index, time_index):
        self.route_src.append(sat_index)
        self.route_time.append(time_index)

    def set_next_hop(self, sat_index, des, next_hop_sat, time_index):
        self.sr_src.append(sat_index)
        self.sr_des.append(des)
        self.sr_target.append(next_hop_sat)
        self.sr_time.append(time_index)
        
    def set_handover(self, src, target, time_index):
        self.handover_srcs.append(src)
        self.handover_targets.append(target)
        self.handover_times.append(time_index)

    def set_ping(self, sat1_index, sat2_index, time_index):
        self.ping_src.append(sat1_index)
        self.ping_des.append(sat2_index)
        self.ping_time.append(time_index)
        
    def set_traceroute(self, src, dst, time_index):
        self.traceroute_src.append(src)
        self.traceroute_dst.append(dst)
        self.traceroute_time.append(time_index)

    def set_perf(self, sat1_index, sat2_index, time_index, target_throughput=None):
        self.perf_src.append(sat1_index)
        self.perf_des.append(sat2_index)
        self.perf_time.append(time_index)
        if target_throughput is None:
            self.perf_throughputs.append(1)
        else:
            self.perf_throughputs.append(target_throughput)

    def start_emulation(self):
        # Start emulation in a new thread.
        sn_thread = sn_Emulation_Start_Thread(
            self.remote_ssh, self.remote_ftp, self.sat_loss,
            self.sat_ground_bandwidth, self.sat_ground_loss, self.assigned_gw, self.demands,
            self.gw_list, self.cell_list, self.container_id_list, self.file_path,
            self.configuration_file_path, self.update_interval,
            self.constellation_size, self.ping_src, self.ping_des,
            self.ping_time, self.handover_srcs, self.handover_targets, self.handover_type,
            self.handover_times, self.sr_src, self.sr_des, self.sr_target,
            self.sr_time, self.damage_ratio, self.damage_time,
            self.damage_list, self.recovery_time, self.route_src,
            self.route_time, self.duration, self.utility_checking_time,
            self.perf_src, self.perf_des, self.perf_time, self.perf_throughputs,
            self.traceroute_src, self.traceroute_dst, self.traceroute_time)
        sn_thread.start()
        sn_thread.join()
        
        # sn_thread.stop_network_traffic()
        # sn_thread.collect_results()

    def stop_emulation(self):
        # Stop emulation in a new thread.
        sn_thread = sn_Emulation_Stop_Thread(self.remote_ssh, self.remote_ftp,
                                             self.file_path)
        sn_thread.start()
        sn_thread.join()

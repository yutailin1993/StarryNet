import os
import threading
import json
import copy
import argparse
import os
from time import sleep
import time
import numpy
import random
import sys
import subprocess
import re
"""
Starrynet utils that are used in sn_synchronizer
author: Yangtao Deng (dengyt21@mails.tsinghua.edu.cn) and Zeqi Lai (zeqilai@tsinghua.edu.cn)
"""
try:
    import threading
except ImportError:
    os.system("pip3 install threading")
    import threading

try:
    import paramiko
except ImportError:
    os.system("pip3 install paramiko")
    import paramiko

try:
    import requests
except ImportError:
    os.system("pip3 install requests")
    import requests


def get_right_satellite(current_sat_id, current_orbit_id, orbit_num):
    if current_orbit_id == orbit_num - 1:
        return [current_sat_id, 0]
    else:
        return [current_sat_id, current_orbit_id + 1]


def get_down_satellite(current_sat_id, current_orbit_id, sat_num):
    if current_sat_id == sat_num - 1:
        return [0, current_orbit_id]
    else:
        return [current_sat_id + 1, current_orbit_id]


def sn_load_file(path, GS_lat_long):
    f = open(path, "r", encoding='utf8')
    table = json.load(f)
    data = {}
    data['cons_name'] = table["Name"]
    data['altitude'] = table["Altitude (km)"]
    data['cycle'] = table["Cycle (s)"]
    data['inclination'] = table["Inclination"]
    data['phase_shift'] = table["Phase shift"]
    data['orbit'] = table["# of orbit"]
    data['sat'] = table["# of satellites"]
    data['link'] = table["Satellite link"]
    data['duration'] = table["Duration (s)"]
    data['ip'] = table["IP version"]
    data['intra_as_routing'] = table["Intra-AS routing"]
    data['inter_as_routing'] = table["Inter-AS routing"]
    data['link_policy'] = table["Link policy"]
    data['handover_policy'] = table["Handover policy"]
    data['update_time'] = table["update_time (s)"]
    data['sat_bw'] = table["satellite link bandwidth (\"X\" Gbps)"]
    data['sat_ground_bw'] = table["sat-ground bandwidth (\"X\" Gbps)"]
    data['sat_loss'] = table["satellite link loss (\"X\"% )"]
    data['sat_ground_loss'] = table["sat-ground loss (\"X\"% )"]
    data['ground_num'] = table["GS number"]
    data['multi_machine'] = table[
        "multi-machine (\"0\" for no, \"1\" for yes)"]
    data['gw_antenna_number'] = table["gw antenna number"]
    data['cell_antenna_number'] = table["cell antenna number"]
    data['antenna_inclination'] = table["antenna_inclination_angle"]
    data['remote_machine_IP'] = table["remote_machine_IP"]
    data['remote_machine_username'] = table["remote_machine_username"]
    data['remote_machine_password'] = table["remote_machine_password"]

    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--cons_name', type=str, default=data['cons_name'])
    parser.add_argument('--satellite_altitude',
                        type=int,
                        default=data['altitude'])
    parser.add_argument('--inclination', type=int, default=data['inclination'])
    parser.add_argument('--orbit_number', type=int, default=data['orbit'])
    parser.add_argument('--sat_number', type=int, default=data['sat'])
    parser.add_argument('--fac_num', type=int, default=len(GS_lat_long))
    parser.add_argument('--link_style', type=str, default=data['link'])
    parser.add_argument('--IP_version', type=str, default=data['ip'])
    parser.add_argument('--link_policy', type=str, default=data['link_policy'])
    # link delay updating granularity
    parser.add_argument('--update_interval',
                        type=int,
                        default=data['update_time'])
    parser.add_argument('--duration', type=int, default=data['duration'])
    parser.add_argument('--inter_routing',
                        type=str,
                        default=data['inter_as_routing'])
    parser.add_argument('--intra_routing',
                        type=str,
                        default=data['intra_as_routing'])
    parser.add_argument('--cycle', type=int, default=data['cycle'])
    parser.add_argument('--time_slot', type=int, default=100)
    parser.add_argument('--sat_bandwidth', type=int, default=data['sat_bw'])
    parser.add_argument('--sat_ground_bandwidth',
                        type=int,
                        default=data['sat_ground_bw'])
    parser.add_argument('--sat_loss', type=int, default=data['sat_loss'])
    parser.add_argument('--sat_ground_loss',
                        type=int,
                        default=data['sat_ground_loss'])
    parser.add_argument('--ground_num', type=int, default=data['ground_num'])
    parser.add_argument('--multi_machine',
                        type=int,
                        default=data['multi_machine'])
    parser.add_argument('--gw_antenna_number',
                        type=int,
                        default=data['gw_antenna_number'])
    parser.add_argument('--cell_antenna_number',
                        type=int,
                        default=data['cell_antenna_number'])
    parser.add_argument('--antenna_inclination',
                        type=int,
                        default=data['antenna_inclination'])
    parser.add_argument('--user_num', type=int, default=0)
    parser.add_argument('--remote_machine_IP',
                        type=str,
                        default=data['remote_machine_IP'])
    parser.add_argument('--remote_machine_username',
                        type=str,
                        default=data['remote_machine_username'])
    parser.add_argument('--remote_machine_password',
                        type=str,
                        default=data['remote_machine_password'])

    parser.add_argument('--path',
                        '-p',
                        type=str,
                        default="starrynet/config.xls")
    parser.add_argument('--hello_interval', '-i', type=int, default=10)
    parser.add_argument('--node_number', '-n', type=int, default=27)
    parser.add_argument('--GS',
                        '-g',
                        type=str,
                        default="50.110924/8.682127/46.635700/14.311817")

    sn_args = parser.parse_args()
    return sn_args


def sn_get_param(file_):
    f = open(file_)
    ADJ = f.readlines()
    for i in range(len(ADJ)):
        ADJ[i] = ADJ[i].strip('\n')
    ADJ = [x.split(',') for x in ADJ]
    f.close()
    return ADJ


def sn_init_remote_machine(host, username, password):
    # transport = paramiko.Transport((host, 22))
    # transport.connect(username=username, password=password)
    remote_machine_ssh = paramiko.SSHClient()
    # remote_machine_ssh._transport = transport
    remote_machine_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    remote_machine_ssh.connect(hostname=host,
                               port=22,
                               username=username,
                               password=password)
    transport = paramiko.Transport((host, 22))
    transport.connect(username=username, password=password)
    return remote_machine_ssh, transport
    # transport.close()


def sn_init_remote_ftp(transport):
    ftp_client = paramiko.SFTPClient.from_transport(transport)  ## ftp client
    return ftp_client


def sn_remote_cmd(remote_ssh, cmd):
    stdin, stdout, stderr = remote_ssh.exec_command(cmd, get_pty=True)
    lines = stdout.readlines()
    return lines


# A thread designed for initializing working directory.
class sn_init_directory_thread(threading.Thread):

    def __init__(self, file_path, configuration_file_path, remote_ssh):
        threading.Thread.__init__(self)
        self.file_path = file_path
        self.remote_ssh = remote_ssh
        self.configuration_file_path = configuration_file_path

    def run(self):
        # Reset docker environment.
        os.system("rm " + self.configuration_file_path + "/" + self.file_path +
                  "/*.txt")
        if os.path.exists(self.file_path + "/mid_files") == False:
            os.system("mkdir " + self.configuration_file_path + "/" +
                      self.file_path)
            os.system("mkdir " + self.configuration_file_path + "/" +
                      self.file_path + "/delay")
            os.system("mkdir " + self.configuration_file_path + "/" +
                      self.file_path + "/mid_files")
        sn_remote_cmd(self.remote_ssh, "mkdir ~/" + self.file_path)
        sn_remote_cmd(self.remote_ssh, "mkdir ~/" + self.file_path + "/delay")


# A thread designed for initializing constellation nodes.
class sn_Node_Init_Thread(threading.Thread):

    def __init__(self, remote_ssh, docker_service_name, node_size,
                 container_id_list, container_global_idx):
        threading.Thread.__init__(self)
        self.remote_ssh = remote_ssh
        self.docker_service_name = docker_service_name
        self.node_size = node_size
        self.container_global_idx = container_global_idx
        self.container_id_list = copy.deepcopy(container_id_list)

    def run(self):

        # Reset docker environment.
        sn_reset_docker_env(self.remote_ssh, self.docker_service_name,
                            self.node_size)
        # Get container list in each machine.
        self.container_id_list = sn_get_container_info(self.remote_ssh)
        # Rename all containers with the global idx
        sn_rename_all_container(self.remote_ssh, self.container_id_list,
                                self.container_global_idx)


def sn_get_container_info(remote_machine_ssh):
    #  Read all container information in all_container_info
    all_container_info = sn_remote_cmd(remote_machine_ssh, "docker ps")
    n_container = len(all_container_info) - 1
    container_id_list = []
    for container_idx in range(1, n_container + 1):
        container_id_list.append(all_container_info[container_idx].split()[0])

    return container_id_list


def sn_delete_remote_network_bridge(remote_ssh):
    all_br_info = sn_remote_cmd(remote_ssh, "docker network ls")
    for line in all_br_info:
        if "La" in line or "Le" in line or "GS" in line:
            network_name = line.split()[1]
            print('docker network rm ' + network_name)
            sn_remote_cmd(remote_ssh, 'docker network rm ' + network_name)


def sn_reset_docker_env(remote_ssh, docker_service_name, node_size):
    print("Reset docker environment for constellation emulation ...")
    print("Remove legacy containers.")
    print(sn_remote_cmd(remote_ssh,
                        "docker service rm " + docker_service_name))
    print(sn_remote_cmd(remote_ssh, "docker rm -f $(docker ps -a -q)"))
    print("Remove legacy emulated ISLs.")
    sn_delete_remote_network_bridge(remote_ssh)
    print("Creating new containers...")
    sn_remote_cmd(
        remote_ssh, "docker service create --replicas " + str(node_size) +
        " --name " + str(docker_service_name) +
        " --cap-add ALL lwsen/starlab_node:1.0 ping www.baidu.com")


def sn_rename_all_container(remote_ssh, container_id_list, new_idx):
    print("Rename all containers ...")
    new_idx = 1
    for container_id in container_id_list:
        sn_remote_cmd(
            remote_ssh, "docker rename " + str(container_id) +
            " ovs_container_" + str(new_idx))
        new_idx = new_idx + 1


# A thread designed for initializing constellation links.
class sn_Link_Init_Thread(threading.Thread):

    def __init__(self, remote_ssh, remote_ftp, orbit_num, sat_num,
                 constellation_size, fac_num, file_path,
                 configuration_file_path, sat_bandwidth, sat_ground_bandwidth,
                 sat_loss, sat_ground_loss):
        threading.Thread.__init__(self)
        self.remote_ssh = remote_ssh
        self.constellation_size = constellation_size
        self.fac_num = fac_num
        self.orbit_num = orbit_num
        self.sat_num = sat_num
        self.file_path = file_path
        self.configuration_file_path = configuration_file_path
        self.sat_bandwidth = sat_bandwidth
        self.sat_ground_bandwidth = sat_ground_bandwidth
        self.sat_loss = sat_loss
        self.sat_ground_loss = sat_ground_loss
        self.remote_ftp = remote_ftp

    def run(self):
        print('Run in link init thread.')
        self.remote_ftp.put(
            os.path.join(os.getcwd(), "starrynet/sn_orchestrater.py"),
            self.file_path + "/sn_orchestrater.py")
        self.remote_ftp.put(
            self.configuration_file_path + "/" + self.file_path +
            '/delay/1.txt', self.file_path + "/1.txt")
        print('Initializing links ...')
        sn_remote_cmd(
            self.remote_ssh, "python3 " + self.file_path +
            "/sn_orchestrater.py" + " " + str(self.orbit_num) + " " +
            str(self.sat_num) + " " + str(self.constellation_size) + " " +
            str(self.fac_num) + " " + str(self.sat_bandwidth) + " " +
            str(self.sat_loss) + " " + str(self.sat_ground_bandwidth) + " " +
            str(self.sat_ground_loss) + " " + self.file_path + "/1.txt")


# A thread designed for initializing bird routing.
class sn_Routing_Init_Thread(threading.Thread):

    def __init__(self, remote_ssh, remote_ftp, orbit_num, sat_num,
                 constellation_size, fac_num, file_path, sat_bandwidth,
                 sat_ground_bandwidth, sat_loss, sat_ground_loss):
        threading.Thread.__init__(self)
        self.remote_ssh = remote_ssh
        self.constellation_size = constellation_size
        self.fac_num = fac_num
        self.orbit_num = orbit_num
        self.sat_num = sat_num
        self.file_path = file_path
        self.sat_bandwidth = sat_bandwidth
        self.sat_ground_bandwidth = sat_ground_bandwidth
        self.sat_loss = sat_loss
        self.sat_ground_loss = sat_ground_loss
        self.remote_ftp = remote_ftp

    def run(self):
        print(
            "Copy bird configuration file to each container and run routing process."
        )
        self.remote_ftp.put(
            os.path.join(os.getcwd(), "starrynet/sn_orchestrater.py"),
            self.file_path + "/sn_orchestrater.py")
        print('Initializing routing ...')
        sn_remote_cmd(
            self.remote_ssh, "python3 " + self.file_path +
            "/sn_orchestrater.py" + " " + str(self.constellation_size) + " " +
            str(self.fac_num) + " " + self.file_path)
        print("Routing initialized!")


# A thread designed for emulation.
class sn_Emulation_Start_Thread(threading.Thread):

    def __init__(self, remote_ssh, remote_ftp, sat_loss, sat_ground_bw,
                 sat_ground_loss, assigned_gw, demands, gw_list, cell_list, container_id_list,
                 file_path, configuration_file_path, update_interval, constellation_size,
                 ping_src, ping_des, ping_time, handover_srcs, handover_targets, handover_type,
                 handover_times, sr_src, sr_des, sr_target, sr_time, damage_ratio, 
                 damage_time, damage_list, recovery_time, route_src, route_time, duration,
                 utility_checking_time, perf_src, perf_des, perf_time, perf_throughputs,
                 traceroute_src, traceroute_dst, traceroute_time):
        threading.Thread.__init__(self)
        self.remote_ssh = remote_ssh
        self.remote_ftp = remote_ftp
        self.sat_loss = sat_loss
        self.sat_ground_bw = sat_ground_bw
        self.sat_ground_loss = sat_ground_loss
        self.assigned_gw = assigned_gw
        self.demands = demands
        self.gw_list = gw_list
        self.cell_list = cell_list
        self.container_id_list = copy.deepcopy(container_id_list)
        self.file_path = file_path
        self.configuration_file_path = configuration_file_path
        self.update_interval = update_interval
        self.constellation_size = constellation_size
        self.ping_src = ping_src
        self.ping_des = ping_des
        self.ping_time = ping_time
        self.handover_srcs = handover_srcs
        self.handover_targets = handover_targets
        self.handover_type = handover_type
        self.handover_times = handover_times
        self.perf_src = perf_src
        self.perf_des = perf_des
        self.perf_time = perf_time
        self.perf_throughputs = perf_throughputs
        self.sr_src = sr_src
        self.sr_des = sr_des
        self.sr_target = sr_target
        self.sr_time = sr_time
        self.damage_ratio = damage_ratio
        self.damage_time = damage_time
        self.damage_list = damage_list
        self.recovery_time = recovery_time
        self.route_src = route_src
        self.route_time = route_time
        self.traceroute_src = traceroute_src
        self.traceroute_dst = traceroute_dst
        self.traceroute_time = traceroute_time
        self.duration = duration
        self.utility_checking_time = utility_checking_time
        if self.container_id_list == []:
            self.container_id_list = sn_get_container_info(self.remote_ssh)

    def _establish_perf(self, src, dst, demand):
        assert dst in self.gw_list
        src_container = self.container_id_list[src - 1]
        gw_container = self.container_id_list[dst - 1]
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        command = ['docker', 'exec', '-d', gw_container, 'bash', '-c',
                   'iperf3 -s -p 5{}'.format(src)]
        subprocess.run(command, capture_output=False, text=True)
        
        command = ['docker', 'exec', '-d', src_container, 'bash', '-c',
                   'iperf3 -c {} -p 5{} -i {} -b {}M -t 0 > /tmp/iperf_{}_{}_result.txt'.format(
                   dst_addr, src, 1.0, demand, src, dst)]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result
    
    def _stop_perf(self, src):
        src_container = self.container_id_list[src - 1]
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c', 
                   'ps aux | grep \'iperf3 -c\' | awk \'{print $2}\'']
        proc_result = subprocess.run(command, capture_output=True, text=True)
        proc_list = proc_result.stdout.split('\n')[:-1]
        
        if len(proc_list) < 2:
            print ("No iperf process found on container " + src_container)
            return
        
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c',
                   'kill {}'.format(proc_list[1])]
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result.stdout, result.stderr
        
    def _establish_ping(self, src, dst):
        assert dst in self.gw_list
        src_container = self.container_id_list[src - 1]
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        command = ['docker', 'exec', '-d', src_container, 'bash', '-c',
                   'ping {} > /tmp/ping_{}_{}_result.txt'.format(
                    dst_addr, src, dst)]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result
    
    def _stop_ping(self, src):
        src_container = self.container_id_list[src - 1]
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c',
                   'ps aux | grep \'ping\' | awk \'{print $2}\'']
        proc_result = subprocess.run(command, capture_output=True, text=True)
        proc_list = proc_result.stdout.split('\n')[:-1]
        if len(proc_list) < 2:
            print ("No ping process found on container " + src_container)
            return
        
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c',
                   'kill {}'.format(proc_list[1])]
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result.stdout, result.stderr
        
    def stop_network_traffic(self):
        for cell in self.cell_list:
            _, _ = self._stop_perf(cell)
            _, _ = self._stop_ping(cell)
    
    def collect_results(self):
        print ("Collecting results...")
        for idx, cell in enumerate(self.cell_list):
            src = cell
            dst = self.gw_list[int(self.assigned_gw[idx])]
            src_container = self.container_id_list[src - 1]
            perf_file = 'iperf_{}_{}_result.txt'.format(src, dst)
            ping_file = 'ping_{}_{}_result.txt'.format(src, dst)
            os.system('docker cp ' + src_container + ':/tmp/' + perf_file + ' ' +
                      './results/iperf/' + perf_file)
            os.system('docker cp ' + src_container + ':/tmp/' + ping_file + ' ' +
                      './results/ping/' + ping_file)
            
    def GSL_link_occupied(self, gs_id):
        container = self.container_id_list[gs_id - 1]
        pattern = r'B{}-eth\d+@'.format(gs_id)
        
        if gs_id in self.gw_list:
            max_link = 3
        else:
            max_link = 1
        
        command = ['docker', 'exec', '-i', container, 'ip', 'addr']
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout
        link_list = re.findall(pattern, output)
        
        if len(link_list) >= max_link:
            return True
        
        return False
            
    def run(self):
        ping_threads = []
        perf_threads = []
        traceroute_threads = []
        timeptr = 2  # current emulating time
        
        # init gateway iperf server
        # for gw in self.gw_list:
        #     print("Setting up iperf server on gateway " + str(gw) + "...")
        #     sn_setup_gw_iperf_server(gw, self.container_id_list, self.remote_ssh)
        #     
        # print ("Wait 30 seconds for iperf server to start...")
        # sleep(10)
            
        for idx, cell in enumerate(self.cell_list):
            print("Setting up iperf client on cell " + str(cell) + "...")
            target_gw = self.gw_list[int(self.assigned_gw[idx])]
            demand = self.demands[idx]
            self._establish_perf(cell, target_gw, demand)
            
        for idx, cell in enumerate(self.cell_list):
            print("Setting up ping on cell " + str(cell) + "...")
            target_gw = self.gw_list[int(self.assigned_gw[idx])]
            self._establish_ping(cell, target_gw)
       
        topo_change_file_path = self.configuration_file_path + "/" + self.file_path + '/Topo_leo_change.txt'
        fi = open(topo_change_file_path, 'r')
        line = fi.readline()
        while line:  # starting reading change information and emulating
            words = line.split()
            if words[0] == 'time':
                print('Emulation in No.' + str(timeptr) + ' second.')
                # the time when the new change occurrs
                current_time = str(int(words[1][:-1]))
                # Wait for user input to stop the script
                # print ("[EXP STOP] Current time: " + str(timeptr))
                # sys.stdin.readline()
                
                while int(current_time) > timeptr:
                    start_time = time.time()
                    if timeptr in self.utility_checking_time:
                        sn_check_utility(
                            timeptr, self.remote_ssh,
                            self.configuration_file_path + "/" +
                            self.file_path)
                    if timeptr % self.update_interval == 0:
                        # updating link delays after link changes
                        sn_update_delay(self.file_path,
                                        self.configuration_file_path, timeptr,
                                        self.constellation_size,
                                        self.remote_ssh, self.remote_ftp)
                    if timeptr in self.damage_time:
                        sn_damage(
                            self.damage_ratio[self.damage_time.index(timeptr)],
                            self.damage_list, self.constellation_size,
                            self.remote_ssh, self.remote_ftp, self.file_path,
                            self.configuration_file_path)
                    if timeptr in self.recovery_time:
                        sn_recover(self.damage_list, self.sat_loss,
                                   self.remote_ssh, self.remote_ftp,
                                   self.file_path,
                                   self.configuration_file_path)
                    if timeptr in self.sr_time:
                        index = [
                            i for i, val in enumerate(self.sr_time)
                            if val == timeptr
                        ]
                        for index_num in index:
                            sn_sr(self.sr_src[index_num],
                                  self.sr_des[index_num],
                                  self.sr_target[index_num],
                                  self.container_id_list, self.remote_ssh)
                    if timeptr in self.handover_times:
                        index = [
                            i for i, val in enumerate(self.handover_times)
                            if val == timeptr
                        ]
                        for index_num in index:
                            cell_id = self.handover_srcs[index_num]
                            target_sat_id = self.handover_targets[index_num]
                            gw = self.gw_list[int(self.assigned_gw[self.cell_list.index(cell_id)])]
                            sn_handover(cell_id,
                                        target_sat_id,
                                        gw,
                                        self.handover_type,
                                        self.constellation_size,
                                        self.container_id_list,
                                        self.file_path,
                                        self.sat_ground_bw,
                                        0,)
                    if timeptr in self.ping_time:
                        if timeptr in self.ping_time:
                            index = [
                                i for i, val in enumerate(self.ping_time)
                                if val == timeptr
                            ]
                            for index_num in index:
                                ping_thread = threading.Thread(
                                    target=sn_ping,
                                    args=(self.ping_src[index_num],
                                          self.ping_des[index_num],
                                          self.ping_time[index_num],
                                          self.constellation_size,
                                          self.container_id_list,
                                          self.file_path,
                                          self.configuration_file_path,
                                          self.remote_ssh))
                                ping_thread.start()
                                ping_threads.append(ping_thread)
                    if timeptr in self.perf_time:
                        if timeptr in self.perf_time:
                            index = [
                                i for i, val in enumerate(self.perf_time)
                                if val == timeptr
                            ]
                            for index_num in index:
                                perf_thread = threading.Thread(
                                    target=sn_perf,
                                    args=(self.perf_src[index_num],
                                          self.perf_des[index_num],
                                          self.perf_time[index_num],
                                          self.perf_throughputs[index_num],
                                          self.gw_list,
                                          self.constellation_size,
                                          self.container_id_list,
                                          self.file_path,
                                          self.configuration_file_path,
                                          self.remote_ssh))
                                perf_thread.start()
                                perf_threads.append(perf_thread)
                    if timeptr in self.traceroute_time:
                        index = [
                            i for i, val in enumerate(self.traceroute_time)
                            if val == timeptr
                        ]
                        for index_num in index:
                            traceroute_thread = threading.Thread(
                                target=sn_traceroute,
                                args=(self.traceroute_src[index_num],
                                      self.traceroute_dst[index_num],
                                      self.traceroute_time[index_num],
                                      self.constellation_size,
                                      self.container_id_list, self.file_path,
                                      self.configuration_file_path,
                                      self.remote_ssh))
                            traceroute_thread.start()
                            traceroute_threads.append(traceroute_thread)
                        
                    if timeptr in self.route_time:
                        index = [
                            i for i, val in enumerate(self.route_time)
                            if val == timeptr
                        ]
                        for index_num in index:
                            sn_route(self.route_src[index_num],
                                     self.route_time[index_num],
                                     self.file_path,
                                     self.configuration_file_path,
                                     self.container_id_list, self.remote_ssh)
                    timeptr += 1
                    end_time = time.time()
                    passed_time = (
                        end_time -
                        start_time) if (end_time - start_time) < 1 else 1
                    sleep(1 - passed_time)
                    if timeptr >= self.duration:
                        return
                    print('Emulation in No.' + str(timeptr) + ' second.')
                print("A change in time " + current_time + ':')
                line = fi.readline()
                words = line.split()
                line = fi.readline()
                line = fi.readline()
                words = line.split()
                while words[0] != 'del:':  # addlink
                    word = words[0].split('-')
                    s = int(word[0])
                    f = int(word[1])
                    if s > f:
                        tmp = s
                        s = f
                        f = tmp
                    print("add link", s, f)
                    # workaround: avoid establishing excessive links
                    # if not self.GSL_link_occupied(f):
                    #     current_topo_path = self.configuration_file_path + "/" + self.file_path + '/delay/' + str(
                    #         current_time) + '.txt'
                    #     matrix = sn_get_param(current_topo_path)
                    #     sn_establish_new_GSL(self.container_id_list, matrix,
                    #                          self.constellation_size,
                    #                          self.sat_ground_bw,
                    #                          self.sat_ground_loss, s, f,
                    #                          self.remote_ssh)
                    current_topo_path = self.configuration_file_path + "/" + self.file_path + '/delay/' + str(
                        current_time) + '.txt'
                    matrix = sn_get_param(current_topo_path)
                    sn_establish_new_GSL(self.container_id_list, matrix,
                                         self.constellation_size,
                                         self.sat_ground_bw,
                                         self.sat_ground_loss, s, f,
                                         self.remote_ssh)
                    line = fi.readline()
                    words = line.split()
                line = fi.readline()
                words = line.split()
                if len(words) == 0:
                    return
                while words[0] != 'time':  # delete link
                    word = words[0].split('-')
                    s = int(word[0])
                    f = int(word[1])
                    if s > f:
                        tmp = s
                        s = f
                        f = tmp
                    print("del link " + str(s) + "-" + str(f) + "\n")
                    sn_del_link(s, f, self.container_id_list, self.remote_ssh)
                    
                    line = fi.readline()
                    words = line.split()
                    if len(words) == 0:
                        return
                if timeptr in self.utility_checking_time:
                    sn_check_utility(
                        timeptr, self.remote_ssh,
                        self.configuration_file_path + "/" + self.file_path)
                if timeptr % self.update_interval == 0:
                    # updating link delays after link changes
                    sn_update_delay(self.file_path,
                                    self.configuration_file_path, timeptr,
                                    self.constellation_size, self.remote_ssh,
                                    self.remote_ftp)
                if timeptr in self.damage_time:
                    sn_damage(
                        self.damage_ratio[self.damage_time.index(timeptr)],
                        self.damage_list, self.constellation_size,
                        self.remote_ssh, self.remote_ftp, self.file_path,
                        self.configuration_file_path)
                if timeptr in self.recovery_time:
                    sn_recover(self.damage_list, self.sat_loss,
                               self.remote_ssh, self.remote_ftp,
                               self.file_path, self.configuration_file_path)
                if timeptr in self.sr_time:
                    index = [
                        i for i, val in enumerate(self.sr_time)
                        if val == timeptr
                    ]
                    for index_num in index:
                        sn_sr(self.sr_src[index_num], self.sr_des[index_num],
                              self.sr_target[index_num],
                              self.container_id_list, self.remote_ssh)
                if timeptr in self.ping_time:
                    if timeptr in self.ping_time:
                        index = [
                            i for i, val in enumerate(self.ping_time)
                            if val == timeptr
                        ]
                        for index_num in index:
                            ping_thread = threading.Thread(
                                target=sn_ping,
                                args=(self.ping_src[index_num],
                                      self.ping_des[index_num],
                                      self.ping_time[index_num],
                                      self.constellation_size,
                                      self.container_id_list, self.file_path,
                                      self.configuration_file_path,
                                      self.remote_ssh))
                            ping_thread.start()
                            ping_threads.append(ping_thread)
                if timeptr in self.perf_time:
                    if timeptr in self.perf_time:
                        index = [
                            i for i, val in enumerate(self.perf_time)
                            if val == timeptr
                        ]
                        for index_num in index:
                            perf_thread = threading.Thread(
                                target=sn_perf,
                                args=(self.perf_src[index_num],
                                      self.perf_des[index_num],
                                      self.perf_time[index_num],
                                      self.perf_throughputs[index_num],
                                      self.gw_list,
                                      self.constellation_size,
                                      self.container_id_list, self.file_path,
                                      self.configuration_file_path,
                                      self.remote_ssh))
                            perf_thread.start()
                            perf_threads.append(perf_thread)
                if timeptr in self.traceroute_time:
                    index = [
                        i for i, val in enumerate(self.traceroute_time)
                        if val == timeptr
                    ]
                    for index_num in index:
                        traceroute_thread = threading.Thread(
                            target=sn_traceroute,
                            args=(self.traceroute_src[index_num],
                                  self.traceroute_dst[index_num],
                                  self.traceroute_time[index_num],
                                  self.constellation_size,
                                  self.container_id_list, self.file_path,
                                  self.configuration_file_path, self.remote_ssh))
                        traceroute_thread.start()
                        traceroute_threads.append(traceroute_thread)
                if timeptr in self.route_time:
                    index = [
                        i for i, val in enumerate(self.route_time)
                        if val == timeptr
                    ]
                    for index_num in index:
                        sn_route(self.route_src[index_num],
                                 self.route_time[index_num], self.file_path,
                                 self.configuration_file_path,
                                 self.container_id_list, self.remote_ssh)
                timeptr += 1  # current emulating time
                time.sleep(0.5)
                if timeptr >= self.duration:
                    return
        fi.close()
        for ping_thread in ping_threads:
            ping_thread.join()
        for perf_thread in perf_threads:
            perf_thread.join()
        for traceroute_thread in traceroute_threads:
            traceroute_thread.join()


def sn_check_utility(time_index, remote_ssh, file_path):
    result = sn_remote_cmd(remote_ssh, "vmstat")
    f = open(file_path + "/utility-info" + "_" + str(time_index) + ".txt", "w")
    f.writelines(result)
    f.close()
    
def sn_setup_gw_iperf_server(gw, container_id_list, remote_ssh):
    sn_remote_cmd(remote_ssh, 'docker exec -id ' + str(container_id_list[gw - 1]) + ' iperf3 -s -p 5201')
    print("iperf server success")
    print("Command: docker exec -id " + str(container_id_list[gw - 1]) + " iperf3 -s -p 5201")

def sn_update_delay(file_path, configuration_file_path, timeptr,
                    constellation_size, remote_ssh,
                    remote_ftp):  # updating delays
    remote_ftp.put(os.path.join(os.getcwd(), "starrynet/sn_orchestrater.py"),
                   file_path + "/sn_orchestrater.py")
    remote_ftp.put(
        configuration_file_path + "/" + file_path + '/delay/' + str(timeptr) +
        '.txt', file_path + '/' + str(timeptr) + '.txt')
    sn_remote_cmd(
        remote_ssh,
        "python3 " + file_path + "/sn_orchestrater.py " + file_path + '/' +
        str(timeptr) + '.txt ' + str(constellation_size) + " update")
    print("Delay updating done.\n")


def sn_damage(ratio, damage_list, constellation_size, remote_ssh, remote_ftp,
              file_path, configuration_file_path):
    print("Randomly setting damaged links...\n")
    random_list = []
    cumulated_damage_list = damage_list
    while len(random_list) < (int(constellation_size * ratio)):
        target = int(random.uniform(0, constellation_size - 1))
        random_list.append(target)
        cumulated_damage_list.append(target)
    numpy.savetxt(
        configuration_file_path + "/" + file_path +
        '/mid_files/damage_list.txt', random_list)
    remote_ftp.put(os.path.join(os.getcwd(), "starrynet/sn_orchestrater.py"),
                   file_path + "/sn_orchestrater.py")
    remote_ftp.put(
        configuration_file_path + "/" + file_path +
        '/mid_files/damage_list.txt', file_path + "/damage_list.txt")
    sn_remote_cmd(remote_ssh,
                  "python3 " + file_path + "/sn_orchestrater.py " + file_path)
    print("Damage done.\n")


def sn_recover(damage_list, sat_loss, remote_ssh, remote_ftp, file_path,
               configuration_file_path):
    print("Recovering damaged links...\n")
    cumulated_damage_list = damage_list
    numpy.savetxt(
        configuration_file_path + "/" + file_path +
        '/mid_files/damage_list.txt', cumulated_damage_list)
    remote_ftp.put(os.path.join(os.getcwd(), "starrynet/sn_orchestrater.py"),
                   file_path + "/sn_orchestrater.py")
    remote_ftp.put(
        configuration_file_path + "/" + file_path +
        '/mid_files/damage_list.txt', file_path + "/damage_list.txt")
    sn_remote_cmd(
        remote_ssh, "python3 " + file_path + "/sn_orchestrater.py " +
        file_path + " " + str(sat_loss))
    cumulated_damage_list.clear()
    print("Link recover done.\n")


def sn_sr(src, des, target, container_id_list, remote_ssh):
    ifconfig_output = sn_remote_cmd(
        remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
        " ifconfig | sed 's/[ \t].*//;/^\(eth0\|\)\(lo\|\)$/d'")
    des_IP = sn_remote_cmd(
        remote_ssh,
        "docker exec -it " + str(container_id_list[des - 1]) + " ifconfig " +
        ifconfig_output[0][:-1] + "|awk -F '[ :]+' 'NR==2{print $4}'")
    target_IP = sn_remote_cmd(
        remote_ssh, "docker exec -it " + str(container_id_list[target - 1]) +
        " ifconfig B" + str(target) + "-eth" + str(src) +
        "|awk -F '[ :]+' 'NR==2{print $4}'")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[src - 1]) +
        " ip route del " + str(des_IP[0][:-3]) + "0/24")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[src - 1]) +
        " ip route add " + str(des_IP[0][:-3]) + "0/24 dev B%d-eth%d via " %
        (src, target) + target_IP[0])
    print("docker exec -d " + str(container_id_list[src - 1]) +
          " ip route add " + str(des_IP[0][:-3]) + "0/24 dev B%d-eth%d via " %
          (src, target) + target_IP[0])


def sn_ping(src, des, time_index, constellation_size, container_id_list,
            file_path, configuration_file_path, remote_ssh):
    if des <= constellation_size:
        ifconfig_output = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig | sed 's/[ \t].*//;/^\(eth0\|\)\(lo\|\)$/d'")
        des_IP = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig " + ifconfig_output[0][:-1] +
            "|awk -F '[ :]+' 'NR==2{print $4}'")
    else:
        des_IP = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig B" + str(des) +
            "-default |awk -F '[ :]+' 'NR==2{print $4}'")
    ping_result = sn_remote_cmd(
        remote_ssh, "docker exec -i " + str(container_id_list[src - 1]) +
        " ping " + str(des_IP[0][:-1]) + " -c 4 -i 0.01 ")
    f = open(
        configuration_file_path + "/" + file_path + "/ping-" + str(src) + "-" +
        str(des) + "_" + str(time_index) + ".txt", "w")
    f.writelines(ping_result)
    f.close()

def calculate_handover_delay(curr_backhaul_delay, target_backhaul_delay, 
                             curr_comm_delay, target_comm_delay, handover_type):
    if handover_type == 'CU':
        delay = 2*curr_comm_delay + 1*target_comm_delay + 6*curr_backhaul_delay + 8*target_backhaul_delay
    elif handover_type == 'DU':
        delay = 2*curr_comm_delay + 1*target_comm_delay + 5*curr_backhaul_delay + 3*target_backhaul_delay
    else:
        raise ValueError("Invalid handover type.")
    
    return delay

def connect_node_to_GSL_link(container_id_list, GSL_name, node_type, sat_id, cell_id,
                             address_16_23, address_8_15, delay, bw, loss):
    if node_type == 'sat':
        last_octet = str(50)
        node_id = sat_id
        interface_name = 'B' + str(sat_id) + '-eth' + str(cell_id)
    elif node_type == 'cell':
        last_octet = str(60)
        node_id = cell_id
        interface_name = 'B' + str(cell_id) + '-eth' + str(sat_id)
    else:
        raise ValueError("Invalid node type.")
    
    os.system('docker network connect ' + GSL_name + ' ' + 
              str(container_id_list[node_id - 1]) + ' --ip 9.' + str(address_16_23) + 
              '.' + str(address_8_15) + '.' + last_octet)
    with os.popen('docker exec -i ' + str(container_id_list[node_id - 1]) +
                  ' ip addr | grep -B 2 9.' + str(address_16_23) + '.' +
                  str(address_8_15) +
                  ".50 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'") as f:
        ifconfig_output = f.readline()
    target_interface = str(ifconfig_output).split('@')[0]
    
    os.system('docker exec -d ' + str(container_id_list[node_id - 1]) +
              ' ip link set dev ' + target_interface + ' down')
    os.system('docker exec -d ' + str(container_id_list[node_id - 1]) +
              ' ip link set dev ' + target_interface + ' name ' + interface_name)
    os.system('docker exec -d ' + str(container_id_list[sat_id - 1]) +
              ' ip link set dev ' + interface_name + ' up')
    os.system('docker exec -d ' + str(container_id_list[sat_id - 1]) +
              ' tc qdisc add dev ' + interface_name +
              ' root net delay ' + str(delay) + 'ms' + ' loss ' + str(loss) + '%'
              ' rate ' + str(bw) + 'Gbps')

def sn_handover_del_GSL_link(container_id_list, cell_id, sat_id):
    GSL_name = 'GSL' + str(sat_id) + '-' + str(cell_id)
    os.system('docker exec -d ' + str(container_id_list[cell_id - 1]) +
              ' ip link set dev B' + str(cell_id) + '-eth' + str(sat_id) + ' down')
    os.system('docker exec -d ' + str(container_id_list[sat_id - 1]) + 
              ' ip link set dev B' + str(sat_id) + '-eth' + str(cell_id) + ' down')
    
    os.system('docker network disconnect ' + GSL_name + ' ' + 
              str(container_id_list[sat_id - 1]))
    os.system('docker network disconnect ' + GSL_name + ' ' +
              str(container_id_list[cell_id - 1]))
    os.system('docker network rm ' + GSL_name)

def sn_handover_establish_GSL_link(container_id_list, constellation_size, delay, 
                          cell_id, sat_id, bw, loss=0):
    address_16_23 = (cell_id - constellation_size) & 0xff
    address_8_15 = sat_id & 0xff
    
    GSL_name = 'GSL' + str(sat_id) + '-' + str(cell_id)
    
    # create docker network for GSL link
    command = 'docker network create ' + GSL_name + ' --subnet 9.' + \
              str(address_16_23) + '.' + str(address_8_15) + '.0/24'
    os.system(command)
    print ('[Handover create GSL:]' + command)
    
    # add sat to GSL link
    connect_node_to_GSL_link(container_id_list, GSL_name, 'sat', sat_id, cell_id,
                             address_16_23, address_8_15, delay, bw, loss)
    
    print ('[Handover added satellite:]' + 'docker network connect ' + GSL_name + ' ' +
           str(container_id_list[sat_id - 1]) + ' --ip 9.' + str(address_16_23) + '.' +
           '.' + str(address_8_15) + '.50')
    
    # add cell to GSL link
    os.system('docker exec -d ' + str(container_id_list[cell_id - 1]) +
              ' ip route del 9.' + str(address_16_23) + '.' + str(address_8_15) + '.0/24')
    
    connect_node_to_GSL_link(container_id_list, GSL_name, 'cell', sat_id, cell_id,
                             address_16_23, address_8_15, delay, bw, loss)
    
    print ('[Handover added cell:]' + 'docker network connect ' + GSL_name + ' ' +
           str(container_id_list[cell_id - 1]) + ' --ip 9.' + str(address_16_23) + '.' +
           '.' + str(address_8_15) + '.60')

def sn_handover(cell_id, target_sat_id, gw, current_time, handover_type, 
                constellation_size, container_id_list, file_dir, bw, loss):
    # load delay matrix
    current_topo_path = file_dir + '/delay/' + str(current_time) + '.txt'
    matrix = sn_get_param(current_topo_path)
    
    with os.popen('docker exec -i ' + str(container_id_list[cell_id - 1]) + 
                  ' ip route | grep 9.{}.{}'.format(gw, gw) + 
                  " | grep -o 'eth[0-9]*' | sed 's/eth//g'") as f:
        current_sat_id = int(f.readline())
    
    # get message delay
    curr_backhaul_delay = matrix[current_sat_id - 1][gw - 1]
    target_backhaul_delay = matrix[target_sat_id - 1][gw - 1]
    curr_comm_delay = matrix[current_sat_id - 1][cell_id - 1]
    target_comm_delay = matrix[target_sat_id - 1][cell_id - 1]
    
    if target_comm_delay == 0:
        print ("[Handover] Target unreachable.")
        return
    
    handover_delay = calculate_handover_delay(curr_backhaul_delay, 
                                              target_backhaul_delay,
                                              curr_comm_delay,
                                              target_comm_delay,
                                              handover_type)
    
    # handover
    # start_time = time.time()
    sn_handover_del_GSL_link(container_id_list, cell_id, current_sat_id)
    # end_time = time.time()
    
    # if handover_delay > end_time - start_time:
    #     sleep(handover_delay - (end_time - start_time))
    sleep(handover_delay)
    
    sn_handover_establish_GSL_link(container_id_list, constellation_size, target_comm_delay,
                                   cell_id, target_sat_id, bw)
    
def sn_perf(src, des, time_index, target_throughput, gw_list, constellation_size, container_id_list,
            file_path, configuration_file_path, remote_ssh):
    if des <= constellation_size:
        ifconfig_output = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig | sed 's/[ \t].*//;/^\(eth0\|\)\(lo\|\)$/d'")
        des_IP = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig " + ifconfig_output[0][:-1] +
            "|awk -F '[ :]+' 'NR==2{print $4}'")
    else:
        des_IP = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig B" + str(des) +
            "-default |awk -F '[ :]+' 'NR==2{print $4}'")

    if des not in gw_list:
        sn_remote_cmd(
            remote_ssh,
            "docker exec -id " + str(container_id_list[des - 1]) + " iperf3 -s ")
        print("iperf server success (on the fly)")

    perf_result = sn_remote_cmd(
        remote_ssh, "docker exec -i " + str(container_id_list[src - 1]) +
        " iperf3 -c " + str(des_IP[0][:-1]) + " -t 5 -b " + str(target_throughput) + "M")
    print("iperf client success")
    
    # DEBUG: perf des ip
    print("des_IP: {}".format(des_IP[0][:-1]))
    # DEBUG: end
    f = open(
        configuration_file_path + "/" + file_path + "/perf-" + str(src) + "-" +
        str(des) + "_" + str(time_index) + ".txt", "w")
    f.writelines(perf_result)
    f.close()
    
def sn_traceroute(src, des, time_index, constellation_size, container_id_list,
                  file_path, configuration_file_path, remote_ssh):
    if des <= constellation_size:
        ifconfig_output = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig | sed 's/[ \t].*//;/^\(eth0\|\)\(lo\|\)$/d'")
        des_IP = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig " + ifconfig_output[0][:-1] +
            "|awk -F '[ :]+' 'NR==2{print $4}'")
    else:
        des_IP = sn_remote_cmd(
            remote_ssh, "docker exec -it " + str(container_id_list[des - 1]) +
            " ifconfig B" + str(des) +
            "-default |awk -F '[ :]+' 'NR==2{print $4}'")
        
    traceroute_result = sn_remote_cmd(
        remote_ssh,
        "docker exec -id " + str(container_id_list[des - 1]) + 
        " traceroute " + str(des_IP[0][:-1]))
    print ("traceroute success")
    
    f = open(configuration_file_path + "/" + file_path + "/traceroute-" + str(src) + "-" +
             str(des) + "_" + str(time_index) + ".txt", "w")
    f.writelines(traceroute_result)
    f.close()


def sn_route(src, time_index, file_path, configuration_file_path,
             container_id_list, remote_ssh):
    route_result = sn_remote_cmd(
        remote_ssh,
        "docker exec -it " + str(container_id_list[src - 1]) + " route ")
    f = open(
        configuration_file_path + "/" + file_path + "/route-" + str(src) +
        "_" + str(time_index) + ".txt", "w")
    f.writelines(route_result)
    f.close()


def sn_establish_new_GSL(container_id_list, matrix, constellation_size, bw,
                         loss, sat_index, GS_index, remote_ssh):
    i = sat_index
    j = GS_index
    # IP address  (there is a link between i and j)
    delay = str(matrix[i - 1][j - 1])
    address_16_23 = (j - constellation_size) & 0xff
    address_8_15 = i & 0xff
    GSL_name = "GSL_" + str(i) + "-" + str(j)
    # Create internal network in docker.
    sn_remote_cmd(
        remote_ssh, 'docker network create ' + GSL_name + " --subnet 9." +
        str(address_16_23) + "." + str(address_8_15) + ".0/24")
    print('[Create GSL:]' + 'docker network create ' + GSL_name +
          " --subnet 9." + str(address_16_23) + "." + str(address_8_15) +
          ".0/24")
    sn_remote_cmd(
        remote_ssh, 'docker network connect ' + GSL_name + " " +
        str(container_id_list[i - 1]) + " --ip 9." + str(address_16_23) + "." +
        str(address_8_15) + ".50")
    ifconfig_output = sn_remote_cmd(
        remote_ssh, "docker exec -it " + str(container_id_list[i - 1]) +
        " ip addr | grep -B 2 9." + str(address_16_23) + "." +
        str(address_8_15) +
        ".50 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'")
    target_interface = str(ifconfig_output[0]).split("@")[0]
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[i - 1]) +
        " ip link set dev " + target_interface + " down")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[i - 1]) +
        " ip link set dev " + target_interface + " name " + "B" +
        str(i - 1 + 1) + "-eth" + str(j))
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[i - 1]) +
        " ip link set dev B" + str(i - 1 + 1) + "-eth" + str(j) + " up")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[i - 1]) +
        " tc qdisc add dev B" + str(i - 1 + 1) + "-eth" + str(j) +
        " root netem delay " + str(delay) + "ms")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[i - 1]) +
        " tc qdisc add dev B" + str(i - 1 + 1) + "-eth" + str(j) +
        " root netem loss " + str(loss) + "%")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[i - 1]) +
        " tc qdisc add dev B" + str(i - 1 + 1) + "-eth" + str(j) +
        " root netem rate " + str(bw) + "Gbps")
    print('[Add current node:]' + 'docker network connect ' + GSL_name + " " +
          str(container_id_list[i - 1]) + " --ip 9." + str(address_16_23) +
          "." + str(address_8_15) + ".50")
    
    # FIXME: workaround to delete the unwanted route added by BIRD
    command_conn = ['docker', 'network', 'connect', GSL_name, container_id_list[j - 1],
                    '--ip', '9.{}.{}.60'.format(address_16_23, address_8_15)]
    result = subprocess.run(command_conn, capture_output=True, text=True)
    while (result.returncode != 0):
        print (result.stderr)
        command_del = ['docker', 'exec', '-d', container_id_list[j - 1], 'ip', 
                       'route', 'del', '9.{}.{}.0/24'.format(address_16_23, address_8_15)]
        subprocess.run(command_del, capture_output=False, text=True)
        result = subprocess.run(command_conn, capture_output=True, text=True)
    
    ifconfig_output = sn_remote_cmd(
        remote_ssh, "docker exec -it " + str(container_id_list[j - 1]) +
        " ip addr | grep -B 2 9." + str(address_16_23) + "." +
        str(address_8_15) +
        ".60 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'")
    target_interface = str(ifconfig_output[0]).split("@")[0]
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[j - 1]) +
        " ip link set dev " + target_interface + " down")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[j - 1]) +
        " ip link set dev " + target_interface + " name " + "B" + str(j) +
        "-eth" + str(i - 1 + 1))
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[j - 1]) +
        " ip link set dev B" + str(j) + "-eth" + str(i - 1 + 1) + " up")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[j - 1]) +
        " tc qdisc add dev B" + str(j) + "-eth" + str(i - 1 + 1) +
        " root netem delay " + str(delay) + "ms")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[j - 1]) +
        " tc qdisc add dev B" + str(j) + "-eth" + str(i - 1 + 1) +
        " root netem loss " + str(loss) + "%")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " + str(container_id_list[j - 1]) +
        " tc qdisc add dev B" + str(j) + "-eth" + str(i - 1 + 1) +
        " root netem rate " + str(bw) + "Gbps")
    print('[Add right node:]' + 'docker network connect ' + GSL_name + " " +
          str(container_id_list[j - 1]) + " --ip 10." + str(address_16_23) +
          "." + str(address_8_15) + ".60")


def sn_del_link(first_index, second_index, container_id_list, remote_ssh):
    sn_remote_cmd(
        remote_ssh, "docker exec -d " +
        str(container_id_list[second_index - 1]) + " ip link set dev B" +
        str(second_index) + "-eth" + str(first_index) + " down")
    sn_remote_cmd(
        remote_ssh, "docker exec -d " +
        str(container_id_list[first_index - 1]) + " ip link set dev B" +
        str(first_index) + "-eth" + str(second_index) + " down")
    GSL_name = "GSL_" + str(first_index) + "-" + str(second_index)
    sn_remote_cmd(
        remote_ssh, 'docker network disconnect ' + GSL_name + " " +
        str(container_id_list[first_index - 1]))
    sn_remote_cmd(
        remote_ssh, 'docker network disconnect ' + GSL_name + " " +
        str(container_id_list[second_index - 1]))
    sn_remote_cmd(remote_ssh, 'docker network rm ' + GSL_name)


# A thread designed for stopping the emulation.
class sn_Emulation_Stop_Thread(threading.Thread):

    def __init__(self, remote_ssh, remote_ftp, file_path):
        threading.Thread.__init__(self)
        self.remote_ssh = remote_ssh
        self.remote_ftp = remote_ftp
        self.file_path = file_path

    def run(self):
        print("Deleting all native bridges and containers...")
        self.remote_ftp.put(
            os.path.join(os.getcwd(), "starrynet/sn_orchestrater.py"),
            self.file_path + "/sn_orchestrater.py")
        sn_remote_cmd(self.remote_ssh,
                      "python3 " + self.file_path + "/sn_orchestrater.py")

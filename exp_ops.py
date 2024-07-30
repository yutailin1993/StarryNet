import argparse
import subprocess
import math
import time
import numpy as np

class ExpOps():
    def __init__(self,
                 current_time,
                 sim_time,
                 user_demands,
                 assignments,
                 results_dir, 
                 gw_indices, 
                 cell_indices,):
        self.current_time = current_time
        self.sim_time = sim_time
        self.user_demands = user_demands
        self.assignments = assignments
        self.results_dir = results_dir
        self.gw_indices = gw_indices
        self.cell_indices = cell_indices
        
        self.container_name_prefix = 'ovs_container_'
        self.perf_client_on = False
        self.set_ping_on = False
        
        self.current_time_idx = int(self.current_time / 5)
        
    def __del__(self):
        if self.perf_client_on:
            self.stop_perf_clients()
    
    def _establish_perf_server(self, src, dst):
        assert dst in self.gw_indices
        gw_container = self.container_name_prefix + str(dst)
        command = ['docker', 'exec', '-d', gw_container, 'bash', '-c', 
                   'iperf3 -s -p 5{}'.format(src)]
        subprocess.run(command, capture_output=False, text=True)
    
    def _establish_perf_client(self, src, dst, demand):
        assert dst in self.gw_indices
        src_container = self.container_name_prefix + str(src)
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        # save iperf results
        command = ['docker', 'exec', '-d', src_container, 'bash', '-c', 
            'iperf3 -c {} -p 5{} -i {} -b {}M -t {} >> /tmp/iperf_{}_results.txt'.format(
            dst_addr, src, 1, demand, math.ceil(self.sim_time), src)]
        
        subprocess.run(command, capture_output=False, text=True)
    
    def _stop_perf_server(self, gw):
        gw_container = self.container_name_prefix + str(gw)
        
        command = ['docker', 'exec', '-i', gw_container, 'bash', '-c', 
                   'ps aux | grep \'iperf3 -c\' | awk \'{print $2}\'']
        process_result = subprocess.run(command, capture_output=True, text=True)
        
        process_list = process_result.stdout.split('\n')[:-1]
        
        for proc in process_list:
            command = ['docker', 'exec', '-i', gw_container, 'bash', '-c',
                       'kill {}'.format(proc)]
            subprocess.run(command, capture_output=False, text=True)
        
    def _stop_perf_client(self, src):
        src_container = self.container_name_prefix + str(src)
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c', 
                   'ps aux | grep \'iperf3 -c\' | awk \'{print $2}\'']
        process_result = subprocess.run(command, capture_output=True, text=True)
        
        process_list = process_result.stdout.split('\n')[:-1]
        
        if len(process_list) < 2:
            print ("No iperf process found on container " + src_container)
            return
        print ("Stop iperf client on cell " + str(src))
        
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c',
                   'kill {}'.format(process_list[1])]
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result.stdout, result.stderr
       
    def _establish_ping(self, src, dst, ping_count=5):
        src_container = self.container_name_prefix + str(src)
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        command = ['docker', 'exec', '-d', src_container, 'bash', '-c',
            'ping -c {} {} >> /tmp/ping_{}_results.txt'.format(
            ping_count, dst_addr, src)]
        
        result = subprocess.run(command, capture_output=False, text=True)
        
        return result
    
    def _establish_traceroute(self, src, dst):
        src_container = self.container_name_prefix + str(src)
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c',
            'traceroute {}'.format(dst_addr)]
       
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result.stdout
    
    def perform_flood(self, dynamic_gw=False):
        for cell_idx, cell in enumerate(self.cell_indices):
            print ("Setting up iperf on cell " + str(cell) + "...")
            src = cell
            if dynamic_gw is True:
                dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
            else:
                dst = self.gw_indices[int(self.assignments[0, cell_idx])]
                
            demand = self.user_demands[self.current_time_idx, cell_idx]
            self._establish_perf_server(src, dst)
            self._establish_perf_client(src, dst, demand)
            
        self.perf_client_on = True
            
    def set_ping(self, dynamic_gw=False):
        for cell_idx, cell in enumerate(self.cell_indices):
            src = cell
            if dynamic_gw is True:
                dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
            else:
                dst = self.gw_indices[int(self.assignments[0, cell_idx])]
            self._establish_ping(src, dst, ping_count=5)
            
        self.set_ping_on = True
       
    def perform_traceroute(self):
        for cell_idx, cell in enumerate(self.cell_indices):
            src = cell
            dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
            file_name = 'traceroute_{}_{}_{}.txt'.format(self.current_time, src, dst)
            
            result = self._establish_traceroute(src, dst)
            
            with open(self.results_dir + 'traceroute/' + file_name, 'w') as file:
                file.writelines(result)
    
    def collect_results(self):
        print ("Collecting results...")
        if self.perf_client_on is True:
            for cell_idx, cell in enumerate(self.cell_indices):
                src = cell
                dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
                src_container = self.container_name_prefix + str(cell)
                result_file = 'iperf_{}_results.txt'.format(src)
                command = ['docker', 'cp', 
                           '{}:/tmp/{}'.format(src_container, result_file), 
                           '{}iperf/{}'.format(self.results_dir, result_file)]

                subprocess.run(command, capture_output=False, text=True)
        
        if self.set_ping_on is True:
            for cell_idx, cell in enumerate(self.cell_indices):
                src = cell
                dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
                src_container = self.container_name_prefix + str(cell)

                result_file = 'ping_{}_results.txt'.format(src)
                command = ['docker', 'cp', 
                           '{}:/tmp/{}'.format(src_container, result_file),
                           '{}ping/{}'.format(self.results_dir, result_file)]

                subprocess.run(command, capture_output=False, text=True)
            
    def stop_perf_clients(self):
        for cell in self.cell_indices:
            src = cell
            _, _ = self._stop_perf_client(src)
            
        for gw in self.gw_indices:
            self._stop_perf_server(gw)
            
        self.perf_client_on = False


def parseargs():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('current_time', type=int, help='Current time in the simulation')
    parser.add_argument('sim_time', type=float, help='Simulation time')
    parser.add_argument('--collect-results', type=int, default=0, help='Collect results')
    parser.add_argument('--results-dir', type=str, 
                        default='./results/',
                        help='Path to the results directory')
    
    args = parser.parse_args()
    return args

def main():
    args = parseargs()
    current_time = args.current_time
    results_dir = args.results_dir
    sim_time = args.sim_time
    
    satellites_num = 200
    
    gw_indices = [x for x in range(satellites_num + 1, satellites_num + 5)]
    cell_indices = [x for x in range(satellites_num + 5, satellites_num + 37)]
    
    # assignments configuration
    assignments_df = np.genfromtxt('./sim_configs/assignment.csv', delimiter=',', skip_header=1)
    assignments_time = assignments_df[:, 0]
    assignments = assignments_df[:, 1:].astype(int)
    
    a = np.array(assignments.shape)
    
    # user demands
    demands_df = np.genfromtxt('./sim_configs/user_demand.csv', delimiter=',', skip_header=1)
    demands_time = demands_df[:, 0]
    demands = demands_df[:, 1:]*10
    
    # initialize
    exp_ops = ExpOps(current_time, sim_time, demands, a, results_dir,
                     gw_indices, cell_indices)
    
    exp_ops.perform_flood(dynamic_gw=False)
    
    print("start traceroute")
    exp_ops.perform_traceroute()
    time.sleep(10)
    print("traceroute done")
    
    print("start ping") 
    exp_ops.set_ping()
    time.sleep(10)
    print("ping done")
    
    # exp_ops.perform_flood(safe_result=True)
    if args.collect_results == 1:
        exp_ops.collect_results()
    
if __name__ == "__main__":
    main()
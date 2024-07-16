import argparse
import subprocess
import time
import numpy as np

class ExpOps():
    def __init__(self,
                 current_time,
                 user_demands,
                 assignments,
                 results_dir, 
                 gw_indices, 
                 cell_indices,):
        self.current_time = current_time
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
    
    def _establish_perf(self, src, dst, demand, safe_result=False):
        assert dst in self.gw_indices
        src_container = self.container_name_prefix + str(src)
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        if not safe_result:
            # do not save iperf results
            command = ['docker', 'exec', '-d', src_container, 'bash', '-c',
                'iperf3 -c {} -p 5201 -i {} -b {}M -t 0'.format(dst_addr, 1.5, demand)]
        else:
            # save iperf results
            command = ['docker', 'exec', '-d', src_container, 'bash', '-c', 
                'iperf3 -c {} -p 5201 -i {} -b {}M -t 0 > /tmp/iperf_{}_{}_{}_results.txt'.format(
                dst_addr, 1.5, demand, self.current_time, src, dst)]
        
        result = subprocess.run(command, capture_output=False, text=True)
        
        return result
    
    def _stop_perf(self, src):
        src_container = self.container_name_prefix + str(src)
        
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c', 'ps aux | grep \'iperf3 -c\' | awk \'{print $2}\'']
        process_result = subprocess.run(command, capture_output=True, text=True)
        
        process_list = process_result.stdout.split('\n')[:-1]
        
        # kill the actual iperf3 process, not the evoked one (bash -c)
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c', 'kill {}'.format(process_list[1])]
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result.stdout, result.stderr
        
    def _establish_ping(self, src, dst, ping_count=5):
        src_container = self.container_name_prefix + str(src)
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        command = ['docker', 'exec', '-d', src_container, 'bash', '-c',
            'ping -c {} {} > /tmp/ping_{}_{}_{}_results.txt'.format(
            ping_count, dst_addr, self.current_time, src, dst)]
        
        result = subprocess.run(command, capture_output=False, text=True)
        
        return result
    
    def _establish_traceroute(self, src, dst):
        src_container = self.container_name_prefix + str(src)
        dst_addr = '9.{}.{}.10'.format(dst, dst)
        
        command = ['docker', 'exec', '-i', src_container, 'bash', '-c',
            'traceroute {}'.format(dst_addr)]
       
        result = subprocess.run(command, capture_output=True, text=True)
        
        return result.stdout
    
    def perform_flood(self, safe_result=False):
        for cell_idx, cell in enumerate(self.cell_indices):
            src = cell
            dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
            demand = self.user_demands[self.current_time_idx, cell_idx]
            self._establish_perf(src, dst, demand, safe_result=safe_result)
            
        self.perf_client_on = True
            
    def set_ping(self):
        for cell_idx, cell in enumerate(self.cell_indices):
            src = cell
            dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
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
        if self.perf_client_on is True:
            for cell_idx, cell in enumerate(self.cell_indices):
                src = cell
                dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
                src_container = self.container_name_prefix + str(cell)
                result_file = 'iperf_{}_{}_{}_results.txt'.format(self.current_time, src, dst)
                command = ['docker', 'cp', 
                           '{}:/tmp/{}'.format(src_container, result_file), 
                           '{}iperf/{}'.format(self.results_dir, result_file)]

                subprocess.run(command, capture_output=False, text=True)
        
        if self.set_ping_on is True:
            for cell_idx, cell in enumerate(self.cell_indices):
                src = cell
                dst = self.gw_indices[int(self.assignments[self.current_time_idx, cell_idx])]
                src_container = self.container_name_prefix + str(cell)

                result_file = 'ping_{}_{}_{}_results.txt'.format(self.current_time, src, dst)
                command = ['docker', 'cp', 
                           '{}:/tmp/{}'.format(src_container, result_file),
                           '{}ping/{}'.format(self.results_dir, result_file)]

                subprocess.run(command, capture_output=False, text=True)
            
    def stop_perf_clients(self):
        for cell in self.cell_indices:
            src = cell
            _, _ = self._stop_perf(src)
            
        self.perf_client_on = False


def parseargs():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('current_time', type=int, help='Current time in the simulation')
    parser.add_argument('--results-dir', type=str, 
                        default='./results/',
                        help='Path to the results directory')
    
    args = parser.parse_args()
    return args

def main():
    args = parseargs()
    current_time = args.current_time
    results_dir = args.results_dir
    
    satellites_num = 200
    
    gw_indices = [x for x in range(satellites_num + 1, satellites_num + 5)]
    cell_indices = [x for x in range(satellites_num + 5, satellites_num + 37)]
    
    # assignments configuration
    assignments_df = np.genfromtxt('./sim_configs/assignment.csv', delimiter=',', skip_header=1)
    assignments_time = assignments_df[:, 0]
    assignments = assignments_df[:, 1:].astype(int)
    
    # user demands
    demands_df = np.genfromtxt('./sim_configs/user_demand.csv', delimiter=',', skip_header=1)
    demands_time = demands_df[:, 0]
    demands = demands_df[:, 1:]
    
    # initialize
    exp_ops = ExpOps(current_time, demands, assignments, results_dir,
                     gw_indices, cell_indices)
    
    print("start traceroute")
    exp_ops.perform_traceroute()
    time.sleep(10)
    print("traceroute done")
    
    print("start ping") 
    exp_ops.set_ping()
    time.sleep(10)
    print("ping done")
    
    # exp_ops.perform_flood(safe_result=True)
    
    exp_ops.collect_results()
    
if __name__ == "__main__":
    main()
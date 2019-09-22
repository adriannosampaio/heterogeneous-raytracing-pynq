import json
import numpy as np
import logging as log
import struct
import application.tracers as tracer
from application.parser import Parser

def save_intersections(filename, ids, intersects):
    with open(filename, 'w') as file:
        for tid, inter in zip(ids, intersects):
            file.write(f'{tid} {inter}\n')

class DarkRendererEdge():

    def __init__(self, config):        
        
        import socket as sk
        self.sock = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.config = config

        # Getting the current ip for binding
        ip   = config['edge']['ip']
        port = config['edge']['port']
        self.addr = (ip, port)
        self.sock.bind(self.addr)
        
        self.connection = None
        self.client_ip = None
        
        self.triangles    = []
        self.triangle_ids = []
        self.rays         = []

        processing = config['processing']
        mode = processing['mode']
        self.heterogeneous_mode = (mode == 'heterogenous')
        self.cpu_active = mode in ['cpu', 'heterogenous']
        self.fpga_active = mode in ['fpga', 'heterogenous']
        
        if self.heterogeneous_mode:
            self.fpga_load_fraction = processing['heterogenous']['fpga-load']

        if self.cpu_active:
            cpu_mode = processing['cpu']['mode']    
            use_python = (cpu_mode == 'python')
            use_multicore = (cpu_mode == 'multicore')
            self.cpu_tracer = tracer.TracerCPU(
                use_multicore=use_multicore,
                use_python=use_python)

        if self.fpga_active:
            fpga_mode = processing['fpga']['mode']
            use_multi_fpga = (fpga_mode == 'multi')
            self.fpga_tracer = tracer.TracerFPGA(
                config['edge']['bitstream'],
                use_multi_fpga=use_multi_fpga)
        
    def cleanup(self):
        self.sock.close()
        
    def start(self):
        from time import time

        log.info("Waiting for client connection")
        self._await_connection()
        
        log.info("Receiving scene file")
        ti = time()
        scene_data = self._receive_scene_data()
        tf = time()
        log.warning(f'Finished receiving data in {tf - ti} seconds')

        log.info('Parsing scene data')
        ti = time()
        self._parse_scene_data(scene_data)
        tf = time()
        log.warning(f'Finished parsing scene data in {tf - ti} seconds')

        log.info('Computing intersection')
        ti = time()
        result = self._compute()
        tf = time()
        log.warning(f'Finishing intersection calculation in {tf - ti} seconds')

        log.info('Preparing and sending results')
        ti = time()
        result = json.dumps(result)
        size = len(result)
        msg = struct.pack('>I', size) + result.encode()
        self.connection.send(msg)
        tf = time()
        log.warning(f'Finished sending results in {tf - ti} seconds')

    def _compute(self):
        import numpy as np
        log.info('Starting edge computation')
        intersects, ids = [], []
        if self.heterogeneous_mode: # currently balancing 50%-50%
            log.info('Computing in heterogeneous mode')
            num_rays = len(self.rays) // 6      

            log.info(f'FPGA processing {self.fpga_load_fraction*100}% (self.fpga_load_fraction)')
            fpga_load = int(np.floor(num_rays * self.fpga_load_fraction))
            log.info(f'FPGA load is {fpga_load}/{num_rays} rays')

            self.fpga_tracer.compute(
                self.rays[:fpga_load*6],
                self.triangle_ids,
                self.triangles)

            cpu_ids, cpu_inter = self.cpu_tracer.compute(
                self.rays[fpga_load*6:],
                self.triangle_ids,
                self.triangles)

            while not self.fpga_tracer.is_done(): pass
            fpga_ids, fpga_inter = self.fpga_tracer.get_results()
            #print(fpga_ids, fpga_inter, cpu_ids, cpu_inter)

            ids = fpga_ids + cpu_ids
            intersects = fpga_inter + cpu_inter

        elif self.fpga_active:
            log.info('Computing in fpga-only mode')
            self.fpga_tracer.compute(
                self.rays,
                self.triangle_ids,
                self.triangles)

            while not self.fpga_tracer.is_done(): 
                pass
            ids, intersects = self.fpga_tracer.get_results()
        else:
            log.info('Computing in cpu-only mode')
            ids, intersects = self.cpu_tracer.compute(
                self.rays,
                self.triangle_ids,
                self.triangles)

        return {
            'intersections' : intersects,
            'triangles_hit' : ids
        } 

    def _await_connection(self):
        self.sock.listen()
        print('Waiting for connection...')
        self.connection, self.current_client = self.sock.accept()
        print(f"Connection with {self.current_client[0]}:{self.current_client[1]}")

    def _receive_scene_data(self):
        log.info("Start reading scene file content")

        raw_size = self.connection.recv(4)
        size = struct.unpack('>I', raw_size)[0]
        log.info(f'Finishing receiving scene file size: {size}B')
        
        CHUNK_SIZE = 256
        full_data = b''
        while len(full_data) < size:
            packet = self.connection.recv(CHUNK_SIZE)
            if not packet:
                break
            full_data += packet
        return full_data.decode()

    NUM_TRIANGLE_ATTRS = 9
    NUM_RAY_ATTRS = 6

    def _parse_scene_data(self, scene_data):
        data = scene_data.split()
        task_data = data[2:]
        self.num_tris = int(data[0])
        self.num_rays = int(data[1])
        tri_end = self.num_tris * (self.NUM_TRIANGLE_ATTRS+1)
        self.triangle_ids = list(map(int, task_data[: self.num_tris]))
        self.triangles    = list(map(float, task_data[self.num_tris : tri_end]))
        self.rays         = list(map(float, task_data[tri_end : ]))


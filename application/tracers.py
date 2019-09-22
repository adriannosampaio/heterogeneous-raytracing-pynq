import numpy as np 
import logging as log
from time import time

class TracerPYNQ:
    MAX_DISTANCE = 1e9
    EPSILON = 1.0e-5
    def compute(self, rays, tri_ids, tris):
        raise Exception('ERROR: Using abstract class')

class XIntersectFPGA():
    
    ADDR_AP_CTRL            = 0x00
    ADDR_I_TNUMBER_DATA     = 0x10
    ADDR_I_TDATA_DATA       = 0x18
    ADDR_I_TIDS_DATA        = 0x20
    ADDR_I_RNUMBER_DATA     = 0x28
    ADDR_I_RDATA_DATA       = 0x30
    ADDR_O_TIDS_DATA        = 0x38
    ADDR_O_TINTERSECTS_DATA = 0x40

    def __init__(self, intersect_ip, name):
        self.intersect_ip = intersect_ip
        self.name = name
        self._out_ids   = None
        self._out_inter = None
        self._tids = None
        self._tris = None
        self._rays = None

    def is_done(self):
        return self.intersect_ip.read(0x00) == 4

    def compute(self, rays, tri_ids, tris):
        from pynq import Xlnk
        xlnk = Xlnk()
        num_tris = len(tris) // 9
        num_rays = len(rays) // 6

        log.info(f'{self.name}: Allocating shared input arrays')
        self._tids = xlnk.cma_array(shape=(num_tris,), dtype=np.int32)
        self._tris = xlnk.cma_array(shape=(num_tris*9,), dtype=np.float64)
        self._rays = xlnk.cma_array(shape=(num_rays*6,), dtype=np.float64)

        log.info(f'{self.name}: Allocating shared output arrays')
        self._out_ids   = xlnk.cma_array(shape=(num_rays,), dtype=np.int32)
        self._out_inter = xlnk.cma_array(shape=(num_rays,), dtype=np.float64)

        log.info(f'{self.name}: Setting accelerator input physical addresses')
        self.intersect_ip.write(self.ADDR_I_TNUMBER_DATA, num_tris)
        self.intersect_ip.write(self.ADDR_I_TDATA_DATA, self._tris.physical_address)
        self.intersect_ip.write(self.ADDR_I_TIDS_DATA, self._tids.physical_address)

        self.intersect_ip.write(self.ADDR_I_RNUMBER_DATA, num_rays)
        self.intersect_ip.write(self.ADDR_I_RDATA_DATA, self._rays.physical_address)
        
        self.intersect_ip.write(self.ADDR_O_TIDS_DATA, self._out_ids.physical_address)
        self.intersect_ip.write(self.ADDR_O_TINTERSECTS_DATA, self._out_inter.physical_address)

        ti = time()
        log.info(f'{self.name}: Filling input memory arrays')
        for t in range(num_tris):
            self._tids[t] = tri_ids[t]
            for i in range(9):
                self._tris[t*9+i] = tris[t*9+i]
        log.info(f'{self.name}: Triangle arrays filled in {time() - ti} seconds')

        ti = time()
        for i, r in enumerate(rays):
            self._rays[i] = r
        log.info(f'{self.name}: Ray arrays filled in {time() - ti} seconds')

        log.info(f'Starting co-processor {self.name}')
        self.intersect_ip.write(0x00, 1)

    def get_results(self):
        return (self._out_ids.tolist(), self._out_inter.tolist())


    
def ray_triangle_intersect(self, ray, tri):
    ''' Implementation of the Möller algorithm for
        ray-triangle intersection calculation
    '''
    origin, direction = np.array(ray[:3]), np.array(ray[3:6])
    v0, v1, v2 = (np.array(tri[3*x: 3*x+3]) for x in range(3))
    EPSILON = 1.0e-5

    edge1 = v1 - v0
    edge2 = v2 - v0

    h = np.cross(direction, edge2)
    a = np.dot(edge1, h)

    if -EPSILON < a < EPSILON:
        return None

    f = 1.0 / a
    s = origin - v0
    u = f * np.dot(s, h)

    if not 0.0 <= u <= 1.0:
        return None

    q = np.cross(s, edge1)
    v = f * np.dot(direction, q)

    if v < 0.0 or u + v > 1.0:
        return None

    t = f * np.dot(edge2, q)

    if EPSILON < t < 1e9:
        return t


class TracerCPU(TracerPYNQ):
    def __init__(self, use_multicore: bool = True, use_python: bool = False):
        self.use_python = use_python
        self.use_multicore = use_multicore

    def compute(self, rays, tri_ids, tris):
        ''' Call the ray-triangle intersection calculation
            method and convert the triangle indentifiers to 
            global

            P.S.: Maybe it's not necessary, since in a CPU is
            faster to pass the ids to the lower level method,
            but I'll change it later
        '''
        intersects, ids = [], []

        if not self.use_python:
            if self.use_multicore: 
                # CPP Code with OpenMP parallelism
                ids, intersects = self._compute_multicore(
                    rays,
                    tri_ids,
                    tris)
            else: 
                # CPP without parallelism
                ids, intersects = self._compute_cpp(
                    rays,
                    tri_ids,
                    tris)
        else: # using the pure python implementation
            ids, intersects = self._compute_python(
                np.array(rays), 
                np.array(tris))
            intersects = intersects.tolist()
            ids = list(map(lambda x : tri_ids[x] if x != -1 else -1, ids))

        return (ids, intersects)

    def _compute_cpp(self, rays, tri_ids, tris):
        import application.bindings.tracer as cpp_tracer
        return cpp_tracer.compute(rays, tri_ids, tris)

    def _compute_multicore(self, rays, tri_ids, tris):
        import application.bindings.tracer as cpp_tracer
        return cpp_tracer.computeParallel(rays, tri_ids, tris)

    def _compute_python(self, rays, triangles):
        ''' Compute the intersection of a set of rays against
            a set of triangles
        '''
        # data structures info
        ray_attrs = 6
        num_rays = len(rays) // ray_attrs
        tri_attrs = 9
        num_tris = len(triangles) // tri_attrs
        # output array
        out_inter = np.full(num_rays, 1.0e9)
        out_ids   = np.full(num_rays, -1)
        # for each ray
        for ray in range(num_rays):
            # select ray
            ray_base = ray * ray_attrs
            closest_tri, closest_dist = -1, self.MAX_DISTANCE
            ray_data = rays[ray_base : ray_base + ray_attrs]

            for tri in range(num_tris):
                tri_base = tri * tri_attrs
            
                tri_data = triangles[tri_base : tri_base + tri_attrs]
            
                dist = ray_triangle_intersect(ray_data, tri_data)
            
                if dist is not None and dist < closest_dist:
                    closest_dist = dist
                    closest_tri  = tri

            out_inter[ray] = closest_dist
            out_ids[ray]   = closest_tri

        return (out_ids, out_inter)



class TracerFPGA(TracerPYNQ):
    def __init__(self, overlay_filename: str, use_multi_fpga: bool = False):
        from pynq import Overlay
        self.use_multi_fpga = use_multi_fpga
        self.accelerators = []

        #overlay = Overlay('/home/xilinx/adrianno/intersect_fpga_x2.bit')
        overlay = Overlay(overlay_filename)
        log.info('Finished loading overlay')
        
        log.info('Initializing FPGA instances')
        self.accelerators.append(
            XIntersectFPGA(overlay.intersectFPGA_0, 'accel_0'))

        if use_multi_fpga:
            log.info('Using multi-accelerator mode')
            self.accelerators.append(
                XIntersectFPGA(overlay.intersectFPGA_1, 'accel_1'))


    def is_done(self):
        all_done = True
        for accel in self.accelerators:
            all_done = all_done and accel.is_done()
        return all_done

    def get_results(self):
        ids, intersects = [], []
        if self.use_multi_fpga:
            ids0, intersects0 = self.accelerators[0].get_results()
            ids1, intersects1 = self.accelerators[1].get_results()
            intersects = intersects0 + intersects1
            ids =  ids0 + ids1
            with open(f'multi_fpga_0.txt', 'w') as file:
                for tid, inter in zip(ids0, intersects0):
                    file.write(f'{tid} {inter}\n')
            with open(f'multi_fpga_1.txt', 'w') as file:
                for tid, inter in zip(ids1, intersects1):
                    file.write(f'{tid} {inter}\n')
        else:
            ids, intersects = self.accelerators[0].get_results()
        return (ids, intersects)

    def compute(self, rays, tri_ids, tris):
        ''' Call the ray-triangle intersection FPGA accelerator

            P.S.: This operation is non-blocking, so it's 
            required to check if the accelerator is finished
            and to get the results manually
        '''
        if self.use_multi_fpga:
            num_rays = len(rays) // 6
            self.accelerators[0].compute(
                rays[ : 6*(num_rays//2)], 
                tri_ids, 
                tris)

            self.accelerators[1].compute(
                rays[6*(num_rays//2) : ], 
                tri_ids, 
                tris)
        else:
            self.accelerators[0].compute(rays, tri_ids, tris)
        
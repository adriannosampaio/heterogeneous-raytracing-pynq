import json
import socket
import struct
import logging as log
from application.parser import Parser
from darkclient import DarkRendererClient
from darkedge import DarkRendererEdge

parser = Parser()

def run_client(config):
	import numpy as np
	from PIL import Image
	from application.raytracer.scene import Scene
	from application.raytracer.geometry import Intersection
	from time import time

	hres, vres = parser.args.res
	psize = parser.args.psize
	
	client = DarkRendererClient(config=config)
	image_name = config['client']['output']
	object_file = config['client']['mesh']
	
	ti = time()
	scene = Scene(object_file)
	scene.set_camera(
		(hres, vres), 
		np.array([0.0, 5.0, 5.0]),
		np.array([0.0, 0.0, 0.3]),
		np.array([0.0, 0.0, 1.0]),
		200, psize)
	log.info(f'Finished standalone setup in {time() - ti} seconds')

	ti = time()
	res = json.loads(client.compute_scene(scene))
	log.info(f'Finished intersection calculations in {time() - ti} seconds')
	
	ti = time()
	final_img = Image.new('RGB', (scene.camera.hres, scene.camera.vres), (0,0,0))
	pix = final_img.load()
	for i, tid in enumerate(res['triangles_hit']):
		x, y = i%scene.camera.hres, i//scene.camera.hres
		pix[x,y] = (0, 0, 0)
		if tid != -1:
			ray = scene.camera.get_ray(x, y)
			it = Intersection(
				ray,
				scene.triangles[tid],
				res['intersections'][i])
			col = (scene.materials[0].shade(it, scene.lights))
			col = tuple((col*255).astype('int32'))
			pix[x,y] = col
	
	log.info(f'Saving {image_name}')
	final_img.save(image_name)
	log.info(f'Finished shading calculations in {time() - ti} seconds')

def run_edge(config):
	dark_node = DarkRendererEdge(config)
	try:
	    dark_node.start()
	finally:
	    dark_node.cleanup()

def main():
	log.basicConfig(
		level=log.WARNING, 
		format='%(levelname)s: [%(asctime)s] - %(message)s', 
		datefmt='%d-%b-%y %H:%M:%S')
	
	config = json.load(open("settings/default.json"))
	log.info(f'Starting in {parser.args.mode} mode')
	if parser.args.mode == 'client':
		run_client(config)
	elif parser.args.mode == 'edge':
		run_edge(config)


if __name__ == '__main__':
	main()
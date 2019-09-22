import os
import sys
import json
import socket
import struct
import logging as log
from application.parser import Parser

class Session:
	def __init__(self, input_filename, output_filename):
		self.input_filename = input_filename
		self.output_filename = output_filename
		
		self.input_file = open(input_filename, 'r')
		line = self.input_file.readline().split()
		self.num_tris = int(line[0])
		self.num_rays = int(line[1])

	def get_tris(self):
		for i in range(self.num_tris):
			yield self.input_file.readline()

	def get_rays(self):
		for i in range(self.num_rays):
			yield self.input_file.readline()

class DarkRendererClient:
	'''	Class responsible for the DarkRenderer client behavior.
		This includes the TCP requests to the Fog/Cloud, task 
		sending and receiving the results.
	'''
	def __init__(self, input_filename=None, output_filename=None, config=None):
		self.sock = socket.socket(
			socket.AF_INET, 
			socket.SOCK_STREAM)
		self.config = config
		
		edge_ip   = config['edge']['ip']
		edge_port = config['edge']['port']
		self.edge_addr = (edge_ip, edge_port)

		log.info(f"Reading filename {input_filename}")
		if input_filename != None:
			self.session = Session(input_filename, output_filename)
			self.num_tris = self.session.num_tris
			self.num_rays = self.session.num_rays

	def _connect(self):
		log.info(f'Connecting to edge node {self.edge_addr[0]}:{self.edge_addr[1]}')
		self.sock.connect(self.edge_addr)

	def _cleanup(self):
		self.sock.close()

	def _send(self, data):
		self.sock.send(data)

	def _recv(self, size):
		msg = self.sock.recv(size)
		return msg

	def compute_scene(self, scene):
		# connect to the edge node
		self._connect()

		# preparing scene to send
		num_tris, num_rays = len(scene.triangles), scene.camera.vres * scene.camera.hres
		string_data  = f'{num_tris} {num_rays}\n' 
		string_data += f'{scene.get_triangles_string()}\n' 
		string_data += f'{scene.camera.get_rays_string()}'

		# sending the scene	
		self._send_scene_string(string_data)

		log.info('Waiting for results')
		result = self._receive_results()
		log.info('Results received')

		self._cleanup()
		return result
		
	def _send_scene_string(self, string):
		log.info('Sending scene configuration')
		size = len(string)
		msg = struct.pack('>I', size) + string.encode()
		self._send(msg)
		log.info("Configuration file sent")

	def _receive_results(self):
		log.info("Start receiving results")

		raw_size = self.sock.recv(4)
		size = struct.unpack('>I', raw_size)[0]
		log.info(f'Finishing receiving scene file size: {size}B')

		CHUNK_SIZE = 256
		full_data = b''
		while len(full_data) < size:
			packet = self._recv(CHUNK_SIZE)
			if not packet:
				break
			full_data += packet
		return full_data.decode()

	def _send_scene_file(self):
		log.info('Sending configuration file')
		with open(self.session.input_filename, 'r') as input_file:
			file = input_file.read()
			size = len(file)
			msg = struct.pack('>I', size) + file.encode()
			self._send(msg)
		log.info("Configuration file sent")

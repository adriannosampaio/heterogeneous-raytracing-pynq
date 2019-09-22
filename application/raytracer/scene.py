from .geometry import *
from .light import *
from .material import *
import numpy as np

def read_obj(filename):
	triangles = []
	vertices = []
	with open(filename, 'r') as file:
		tid = 0
		vcount = 0
		for line in file:
			line = line.split()
			data_type = line[0]
			data = line[1:]
			if data_type == 'v':
				vcount += 1
				vertices.append(np.array(list(map(float, data))))
			elif data_type == 'f':
				triangles.append(
					Triangle(
						vertices[int(data[0]) - 1],
						vertices[int(data[1]) - 1],
						vertices[int(data[2]) - 1])
					)
				triangles[tid].id = tid
				tid+=1
	return triangles

class Scene():
	def __init__(self, filename):
		self.triangles = read_obj(filename)
		self.lights = [
			PointLight(
				np.array([50., 50., 50.]),
				np.array([1.0, 1.0, 1.0]),
				2.0),
			PointLight(
				np.array([-50., -50., 50.]),
				np.array([1.0, 1.0, 1.0]),
				1.0)]
		self.camera = None
		self.materials = [Matte(np.array([1.0, 0.0, 1.0]), 0.7)]

	def set_camera(self, resolution : tuple, 
		eye_point : np.ndarray, look_point : np.ndarray,
		up_vector : np.ndarray, distance : float, 
		psize : float):
		
		self.camera = Camera(
			resolution, 
			eye_point,
			look_point,
			up_vector,
			distance, 
			psize)

	def get_triangles_string(self):
		ids = ''
		out = ''
		counter = 0
		for t in self.triangles:
			ids += f'{counter} '
			for p in t.pts:
				for c in p:
					out += f'{c} '
			out += '\n'
			counter += 1
		return ids + '\n' + out + '\n'

class Camera():
	def __init__(self, 
		res, eye_point, 
		look_point, up_vec, 
		dist, psize):

		self.hres, self.vres = res
		self.dist = dist
		self.psize = psize
		self.eye_point = eye_point
		self.look_point = look_point
		self.up_vec = up_vec

		self.w  = eye_point - look_point
		self.w /= np.linalg.norm(self.w)
		
		self.u = -np.cross(up_vec, self.w)
		self.u /= np.linalg.norm(self.u)

		self.v = np.cross(self.w, self.u)

	def get_ray(self, c, r):
		xv = self.psize*(c - self.hres/2),
		yv = self.psize*(r - self.vres/2);
		d = xv*self.u + yv*self.v - self.dist*self.w
		d /= np.linalg.norm(d)
		return Ray(self.eye_point, d)

	def get_rays_string(self):
		out = ''
		for r in range(self.vres):
			for c in range(self.hres):
				xv = self.psize*(c - self.hres/2),
				yv = self.psize*(r - self.vres/2);
				dir = xv*self.u + yv*self.v - self.dist*self.w
				dir /= np.linalg.norm(dir)

				for i in self.eye_point:
					out += f'{round(i, 6)} '
				for i in dir:
					out += f'{round(i, 6)} '
				out += '\n'
		return out

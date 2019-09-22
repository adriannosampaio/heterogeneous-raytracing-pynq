import numpy as np 

class Intersection():
	def __init__(self, ray, tri=None, distance=np.inf):
		if tri == None:
			self.hit = False
		else:
			self.hit = True
			self.hit_point = ray.get_point(distance)
			self.distance = distance
			self.normal = tri.normal
			self.tri = tri
			self.incident_direction = -ray.d
			self.triangle_id = tri.get_id()


class Ray(object):
	"""docstring for Ray"""

	LAST_RAY_ID = 0

	def __init__(self, origin, direction, material_id=0):
		self._id = self.LAST_RAY_ID
		self.LAST_RAY_ID += 1
		self.origin = origin
		self.o = origin
		self.direction = direction
		self.d = direction

	def get_point(self, distance):
		return self.o + self.d*distance

class Object():
	LAST_OBJ_ID = 0
	def __init__(self):
		self.id = self.LAST_OBJ_ID
		self.LAST_OBJ_ID += 1

	def get_id(self):
		return self.id

	def intersect(self, ray):
		pass

	def get_normal(self, intersection):
		pass

class Triangle(Object):

	def __init__(self, p1, p2, p3):
		super().__init__()
		self.p1 = p1	
		self.p2 = p2
		self.p3 = p3
		self.pts = (p1, p2, p3)
		self.normal = np.cross(p2 - p1, p3 - p1)
		self.normal /= np.linalg.norm(self.normal)

	def __repr__(self):
		p1 = f'({self.p1}), '
		p2 = f'({self.p2}), '
		p3 = f'({self.p3})>, '
		normal = f'({self.normal})>, '

		return f'<Triangle {self.id} ' + p1 + p2 + p3 + normal + '>\n'

	def get_normal(self):
		return self.normal

	def intersect(self, ray):
		''' Implementation of the Möller algorithm for
		ray-triangle intersection calculation
		'''
		origin, direction = ray,o, ray.d
		v0, v1, v2 = self.p1, self.p2, self.p3

		edge1 = v1 - v0
		edge2 = v2 - v0

		h = np.cross(direction, edge2)
		a = np.dot(edge1, h)

		if -self.EPSILON < a < self.EPSILON:
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

		if self.EPSILON < t < 1e9:
			return t



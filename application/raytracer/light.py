import numpy as np 

class LightSource(object):
	def get_direction(self, point):
		return None

	def get_luminance(self):
		return None

class PointLight(LightSource):
	"""docstring for LightSource"""
	def __init__(self, position, color, intensity):
		self.position	= position
		self.color		= color
		self.intensity 	= intensity

	def get_direction(self, point):
		return self.position - point

	def get_radiance(self):
		return self.color * self.intensity

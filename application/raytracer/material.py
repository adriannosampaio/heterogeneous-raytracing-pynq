import numpy as np

INV_PI = 1.0 / np.pi

class Matte(object):
	"""docstring for Matte"""
	def __init__(self, color, diffusion_coef):
		self.color = color
		self.diffuse_coef = diffusion_coef

	def shade(self, it, lights):
		color = np.zeros(3)
		for light in lights:
			wi = light.get_direction(it.hit_point)
			wo = it.incident_direction
			influence = light.get_radiance()
			dot = np.dot(wo, it.normal)
			L = self.color*self.diffuse_coef*influence*dot*INV_PI			#print('L ',L)
			color += L
		return color



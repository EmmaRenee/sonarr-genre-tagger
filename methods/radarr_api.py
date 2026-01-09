from pyarr.radarr import RadarrAPI


class Radarr(object):
	def __init__(self, url: str, apikey: str):
		# Normalize provided URL: strip any trailing /api or /api/v3 so
		# pyarr can append its own API path correctly.
		host = url.rstrip('/')
		if host.endswith('/api/v3'):
			host = host[: -len('/api/v3')]
		elif host.endswith('/api'):
			host = host[: -len('/api')]
		self.api = RadarrAPI(host_url=host, api_key=apikey)

	def update_movie(self, movie_id, data: dict):
		return self.api.upd_movie(data)
	
	def add_tag(self, tag: str):
		return self.api.create_tag(label=tag)

	def get_movies(self):
		return self.api.get_movie()

	def get_tags(self):
		# pyarr historically exposed either `get_tags` or `get_tag` depending
		# on version; prefer `get_tags` if available, otherwise fall back.
		if hasattr(self.api, 'get_tags'):
			return self.api.get_tags()
		return self.api.get_tag()

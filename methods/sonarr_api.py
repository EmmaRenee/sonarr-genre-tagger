from pyarr.sonarr import SonarrAPI
# import time
# import json
# import requests


class Sonarr(object):
	def __init__(self, url: str, apikey: str):
		# Normalize provided URL: strip any trailing /api or /api/v3 so
		# pyarr can append its own API path correctly.
		host = url.rstrip('/')
		if host.endswith('/api/v3'):
			host = host[: -len('/api/v3')]
		elif host.endswith('/api'):
			host = host[: -len('/api')]
		self.api = SonarrAPI(host_url=host, api_key=apikey)
		# self.api_key = apikey
		# self.host_url = url
		# self.api_suffix = "api/v3"

	# def sonarr_api_request(self, url, request_type = "get", data = dict()):
	# 	backoff_timer = 2
	# 	payload = json.dumps(data)
	# 	request_payload = dict()
	# 	headers = {
	# 		'X-Api-Key': self.api_key,
	#         "Content-Type": "application/json",
	#         "accept": "application/json",
	# 	}
	# 	if request_type not in ["post", "put", "delete"]:
	# 		request_payload = requests.get(url, headers = headers, data = payload)
	# 	elif request_type == "put":
	# 		request_payload = requests.put(url, headers = headers, data = payload)
	# 	elif request_type == "post":
	# 		request_payload = requests.post(url, headers = headers, data = payload)
	# 	elif request_type == "delete":
	# 		request_payload = requests.delete(url, headers = headers, data = payload)
	# 	time.sleep(backoff_timer)
	# 	return request_payload.json()

	def update_series(self, series_id, data: dict):
		return self.api.upd_series(data)
	
	def add_tag(self, tag: str):
		return self.api.create_tag(label=tag)

	def get_series(self):
		# return self.sonarr_api_request(f"{self.host_url}/api/v3/series") 
		# ?includeSeasonImages=false")
		return self.api.get_series()

	def get_tags(self):
		# pyarr historically exposed either `get_tags` or `get_tag` depending
		# on version; prefer `get_tags` if available, otherwise fall back.
		if hasattr(self.api, 'get_tags'):
			return self.api.get_tags()
		return self.api.get_tag()
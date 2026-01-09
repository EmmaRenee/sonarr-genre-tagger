#!/usr/bin/env python3
from methods.sonarr_api import Sonarr
from methods.radarr_api import Radarr
from pathlib import Path
import json
import logging
import os
import subprocess
import yaml
import urllib.request

def ensure_anime_database(log):
	"""Download the latest anime database if not present or update if needed."""
	db_path = Path("/config/anime-offline-database/anime-offline-database-minified.json")
	db_dir = db_path.parent
	db_dir.mkdir(parents=True, exist_ok=True)
	
	db_url = "https://github.com/manami-project/anime-offline-database/releases/download/latest/anime-offline-database-minified.json"
	
	try:
		log.info("Downloading latest anime database...")
		urllib.request.urlretrieve(db_url, db_path)
		log.info(f"Successfully downloaded anime database to {db_path}")
	except Exception as e:
		log.error(f"Failed to download anime database: {e}")
		if not db_path.exists():
			log.error("Anime database not available and download failed. Cannot continue.")
			raise
		log.warning("Using cached anime database")

		
class Shows(object):
	def __init__(self, config: object):
		self.tags = config.sonarr.get_tags()
		self.series = config.sonarr.get_series()
		self.anidb = json.loads(open(Path(f"/config/anime-offline-database/anime-offline-database-minified.json")).read())["data"]
		self.aggregate = list()
		self.drop_tags = config.file["tagging"].get("drop", [])
		self.replacement_tags = config.file["tagging"].get("replacements", {})
		self.replacement_tags[" "] = "_" # this doesnt translate nice from a configmap so I injected it; besides tags don't accept spacing in sonarr

class Movies(object):
	def __init__(self, config: object):
		self.tags = config.radarr.get_tags()
		self.movie_list = config.radarr.get_movies()
		self.anidb = json.loads(open(Path(f"/config/anime-offline-database/anime-offline-database-minified.json")).read())["data"]
		self.aggregate = list()
		self.drop_tags = config.file["tagging"].get("drop", [])
		self.replacement_tags = config.file["tagging"].get("replacements", {})
		self.replacement_tags[" "] = "_"

class Show(object):
	def __init__(self, show: dict):
		self.title = show.get("title")
		self.tags = unique(show.get("genres", []))
		self.tag_ids = unique(show.get("tags", []))
		self.id = show.get("id")
		self.sonarr = dict()
		self.type = show.get("seriesType")

class Movie(object):
	def __init__(self, movie: dict):
		self.title = movie.get("title")
		self.tags = unique(movie.get("genres", []))
		self.tag_ids = unique(movie.get("tags", []))
		self.id = movie.get("id")
		self.radarr = dict()
		self.type = "anime" if any(genre.lower() == "anime" for genre in movie.get("genres", [])) else "live-action"

class Config:
	def __init__(self, config_file="/config/config.yaml"):
		self.file = yaml.load(open(config_file), Loader=yaml.FullLoader) if os.path.exists(Path(config_file)) else {"tagging": {"drop": [], "replacements": {}}}
		self.log = logging
		self.log.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
		# Ensure anime database is available
		ensure_anime_database(self.log)
		self.sonarr = Sonarr(url=os.environ.get("SONARR_URL", ""), apikey=os.environ.get("SONARR_API", ""))
		self.radarr = Radarr(url=os.environ.get("RADARR_URL", ""), apikey=os.environ.get("RADARR_API", "")) if os.environ.get("RADARR_URL") else None
		self.shows = Shows(config=self) if os.environ.get("SONARR_API") else None
		self.movies = Movies(config=self) if os.environ.get("RADARR_API") else None
		if self.shows:
			self.parser_sonarr()
		if self.movies:
			self.parser_radarr()

	def parser_sonarr(self):
		self.shows.tags = self.sonarr.get_tags()
		previous_tags = self.shows.tags
		for s in self.shows.series:
			show = Show(s)
			if show.type == "anime":
				show.tags += ["anime", "animated", "animation", "japanese"]
				for anime in self.shows.anidb:
					if anime["title"] == show.title:
						show.tags += anime["tags"]
						break
			show.tags = unique([cleanup_tags(tag=i, replacements=self.shows.replacement_tags) for i in sorted(list(set(show.tags)))])
			self.shows.aggregate.append(show)
			self.write_tags_sonarr(show)
		self.log.info("Sonarr Work Complete")

	def parser_radarr(self):
		self.movies.tags = self.radarr.get_tags()
		previous_tags = self.movies.tags
		for m in self.movies.movie_list:
			movie = Movie(m)
			if movie.type == "anime":
				movie.tags += ["anime", "animated", "animation", "japanese"]
				for anime in self.movies.anidb:
					if anime["title"] == movie.title:
						movie.tags += anime["tags"]
						break
			movie.tags = unique([cleanup_tags(tag=i, replacements=self.movies.replacement_tags) for i in sorted(list(set(movie.tags)))])
			self.movies.aggregate.append(movie)
			self.write_tags_radarr(movie)
		self.log.info("Radarr Work Complete")

	def write_tags_sonarr(self, show):
		self.log.info(f"Processing tags for {show.title}")
		show.sonarr = [tvShow for tvShow in self.shows.series if tvShow["title"]==show.title][0]
		add_tags(tags=aggregate_tags(drop_tags=self.shows.drop_tags, input_tags=show.tags), tagmap=self.sonarr.get_tags(), sonarr=self.sonarr)
		try:
			self.shows.tags = self.sonarr.get_tags()
		except:
			self.shows.tags = previous_tags
		[show.tags.remove(i) for i in show.tags if i in self.shows.drop_tags]
		show.tag_ids = unique([i.get("id") for i in self.shows.tags if (i.get("label") in show.tags)])
		show.sonarr.update({"tags": show.tag_ids})
		self.log.info(f"Tagging has started for {show.title}:\t{show.tags}")
		self.log.info(self.sonarr.update_series(series_id=show.id, data=show.sonarr))
		self.log.info(f"Tagging has completed for {show.title}")
		try:
			self.log.info(f"Tagging has started for {show.title}:\t{show.tags}")
			self.log.debug(self.sonarr.update_series(series_id=show.id, data=show.sonarr))
			self.log.info(f"Tagging has completed for {show.title}")
		except:
			pass

	def write_tags_radarr(self, movie):
		self.log.info(f"Processing tags for {movie.title}")
		movie.radarr = [mov for mov in self.movies.movie_list if mov["title"]==movie.title][0]
		add_tags(tags=aggregate_tags(drop_tags=self.movies.drop_tags, input_tags=movie.tags), tagmap=self.radarr.get_tags(), sonarr=self.radarr)
		try:
			self.movies.tags = self.radarr.get_tags()
		except:
			self.movies.tags = previous_tags
		[movie.tags.remove(i) for i in movie.tags if i in self.movies.drop_tags]
		movie.tag_ids = unique([i.get("id") for i in self.movies.tags if (i.get("label") in movie.tags)])
		movie.radarr.update({"tags": movie.tag_ids})
		self.log.info(f"Tagging has started for {movie.title}:\t{movie.tags}")
		self.log.info(self.radarr.update_movie(movie_id=movie.id, data=movie.radarr))
		self.log.info(f"Tagging has completed for {movie.title}")
		try:
			self.log.info(f"Tagging has started for {movie.title}:\t{movie.tags}")
			self.log.debug(self.radarr.update_movie(movie_id=movie.id, data=movie.radarr))
			self.log.info(f"Tagging has completed for {movie.title}")
		except:
			pass

def cleanup_tags(tag: str, replacements: dict):
	tag = tag.lower()
	if tag.endswith("ss"):
		tag = tag.rstrip(tag[-1])
	for before, after in replacements.items():
		tag = tag.replace(before, after)
	return tag

def aggregate_tags(drop_tags: list, input_tags: list):
	return unique([tag for tag_list in input_tags for tag in (tag_list if isinstance(tag_list, list) else [tag_list]) if tag not in drop_tags])

def add_tags(tags: list, tagmap: object, sonarr: object):
	for tag in tags:
		found = False
		for i in tagmap:
			if i["label"] == tag:
				found = True
				break
		if not found:
			try:
				sonarr.add_tag(tag)
				logging.info(f"+ success adding tag {tag}")
			except Exception as e:
				logging.error(f"Failed to add tag {tag}: {e}")

def unique(tags):
	return sorted(list(set(tags)))


if __name__ == "__main__":
	config = Config()
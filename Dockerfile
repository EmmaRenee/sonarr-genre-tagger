FROM 	python:3.12-alpine 
LABEL 	maintainer='Jacob Dresdale' name=sonarr-genre-tagger version=1.7
USER 	root
VOLUME 	/config
WORKDIR /config
COPY 	. /config/

# Add build dependencies
RUN 	apk add --no-cache --virtual .build-deps \
    	gcc musl-dev && \
    	pip install --upgrade pip && \
    	pip install -r requirements.txt && \
    	apk del .build-deps && \
			apk add --no-cache bash \
				openssh
ENV 	SONARR_URL=""
ENV		SONARR_API=""
ENV		RADARR_URL=""
ENV		RADARR_API=""
RUN 	chmod +x main.py
CMD 	["python", "/config/main.py"]
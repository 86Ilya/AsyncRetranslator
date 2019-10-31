#!/bin/bash

function finish() {
        echo "Exiting"
	docker-compose -f docker-compose-demo.yml down
}

trap finish SIGINT

docker-compose -f docker-compose-demo.yml build
docker-compose -f docker-compose-demo.yml up

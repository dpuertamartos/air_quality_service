#!/bin/bash


app_name="air-quality-microservice"
username="dpuertamartos"
tag="latest"

architectures="linux/amd64"

# Navigate to the directory where the Dockerfile is located
cd "$(dirname "$0")"

if docker buildx ls | grep -q mybuilder; then
    docker buildx rm mybuilder
fi

docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap
docker buildx build -f Dockerfile -t $username/$app_name:$tag --platform $architectures --push .

docker buildx rm mybuilder
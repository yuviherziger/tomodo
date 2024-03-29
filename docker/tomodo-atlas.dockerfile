ARG IMAGE_REPO=mongodb/atlas
ARG IMAGE_TAG=v1.15.1
FROM $IMAGE_REPO:$IMAGE_TAG

ARG PORT=27017
ARG NAME=local-deployment
ENV MDBVERSION=7.0

ENTRYPOINT atlas deployments setup ${NAME} --type local --bindIpAll --force \
    ${USERNAME:+--username $USERNAME} \
    ${PASSWORD:+--password $PASSWORD} \
    ${MDBVERSION:+--mdbVersion $MDBVERSION} \
    --port ${PORT} --skipMongosh & tail -f /dev/null

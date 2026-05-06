#!/bin/bash -x

function init_mysql(){
    set -x
    DONE_FILE="${CONTAINER_BASE_DIRECTORY}/${SHARED_DIRECTORY}/mysql-${DONE_FILE_NAME}"
    [ -e "${DONE_FILE}" ]  && return 0
    sed -i -e '/datadir.*=/s/#//' /etc/mysql/mariadb.conf.d/50-server.cnf

    docker-entrypoint.sh mariadbd & sleep 20;

    for directory in ${MYSQL_DIRECTORIES//#/ /}; do
        echo "rsync-ing directory ${directory}"
        ls "${directory}"
        target="${CONTAINER_BASE_DIRECTORY}/${MYSQL_BASE_DIRECTORY}/${directory}"
        mkdir -p "${target}"
        rsync -avuP "/${directory}/" "${target}/"

    done
    touch "${DONE_FILE}"
}

while getopts mn OPTARG; do
    case "${OPTARG}" in
        m)
            init_mysql;
        ;;
        *)
            echo "No option ${OPTARG} available"
        ;;
    esac
done

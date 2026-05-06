#!/bin/bash -xue
# shellcheck disable=SC2016

export E="${E:-}"
export DEBUG="${DEBUG:-}"
export DONE_FILE_NAME="SETUP_COMPLETE"
# shellcheck disable=SC2155,SC2046,SC2086
export LOCAL_BASE_DIRECTORY=$(dirname $(realpath $0))
export DELAY="${DELAY:-20}"
export DAEMONIZE="-d --wait"
export CONTAINERS_PRESERVE="${CONTAINERS_PRESERVE:-false}"
export BE_COMPOSE_FILE="${BE_COMPOSE_FILE:-docker-compose-backend.yml}"
export COMPOSE_COMMAND="${COMPOSE_COMMAND:-"docker compose"}"
export MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-password}"
export CONTAINER_BASE_DIRECTORY="/media/backup"
export UI_BASE_DIRECTORY="${UI_BASE_DIRECTORY:-nginx}"
export MOUNTS_DIRECTORY="mounts"
export MYSQL_BASE_DIRECTORY="mysql"
export SHARED_DIRECTORY="shared"
export BE_COMPOSE_FILE_FULLPATH="${LOCAL_BASE_DIRECTORY}"/"${BE_COMPOSE_FILE}"

# shellcheck disable=SC2155
export MYSQL_DIRECTORIES=$(
    echo \
        "var/lib/mysql" \
        "var/log/mysql" \
        "etc/mysql" \
    | sed -e "s/\s\+/#/g"
)

# shellcheck disable=SC2089
MYSQL_LOCAL_BASE='"${LOCAL_BASE_DIRECTORY}"/"${MOUNTS_DIRECTORY}"/"${MYSQL_BASE_DIRECTORY}"'
# shellcheck disable=SC2089
SHARED_LOCAL_BASE='"${LOCAL_BASE_DIRECTORY}"/"${MOUNTS_DIRECTORY}"/"${SHARED_DIRECTORY}"'


# TODO update
function usage(){
    cat <<END
    USAGE: $0 [-h] [-d] [-f] [-p] -i|-k|-S|-D
    -h              Print this help message and exit
    -d              Activate debug mode
    -n              Report values and exit
    -f              Foreground  - Do not daemonize (must preceed execution option)
    -p              Preserve containers - store container data on host. If not destroy will reset contents.
    -i              Initialise the database containers
    -F              Set the docker compose file to use. Default: "${BE_COMPOSE_FILE}"
    -k              Stop containers
    -S              Start containers
    -D              Destroy (delete) containers
END
exit "${1}"
}

# TODO update
function report_values(){
    cat <<END
    BASEDIR="${BASEDIR}"
    MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD}"
    HOST_BASE="${HOST_BASE}"
    CONTAINER_BASE="${CONTAINER_BASE}"
    DAEMONIZE="${DAEMONIZE}"
    COMPOSE_COMMAND="${COMPOSE_COMMAND}"
    CONTAINERS_PRESERVE="${CONTAINERS_PRESERVE}"
    BE_COMPOSE_FILE_FULLPATH="${BE_COMPOSE_FILE_FULLPATH}"
END
}

function recreate_directories(){
    "${E}" sudo rm -rf "${LOCAL_BASE_DIRECTORY}"/"${MOUNTS_DIRECTORY}"/"${MYSQL_BASE_DIRECTORY}"/*
    "${E}" sudo rm -rf "${LOCAL_BASE_DIRECTORY}"/"${MOUNTS_DIRECTORY}"/"${SHARED_DIRECTORY}"/*"${DONE_FILE_NAME}"

    for directory in ${MYSQL_DIRECTORIES//#/ /}; do
        sudo mkdir -p "${LOCAL_BASE_DIRECTORY}"/"${MOUNTS_DIRECTORY}"/"${MYSQL_BASE_DIRECTORY}"/"${directory}"
    done

}

function output_mysql_data(){
# shellcheck disable=SC2016
    set +x
    echo "For mysql container"
    echo "==================="
    echo "  environment:"
    echo '    MARIADB_ROOT_PASSWORD: "${MARIADB_ROOT_PASSWORD}"'
    echo '    LOCAL_BASE_DIRECTORY: "${LOCAL_BASE_DIRECTORY}"'
    echo '    CONTAINER_BASE_DIRECTORY: "${CONTAINER_BASE_DIRECTORY}"'
    echo '    MYSQL_BASE_DIRECTORY: "${MYSQL_BASE_DIRECTORY}"'
    echo '    MOUNTS_DIRECTORY: "${MOUNTS_DIRECTORY}"'

    echo "  volumes:"
    for directory in ${MYSQL_DIRECTORIES//#/ /}; do
        echo "    - \"${MYSQL_LOCAL_BASE}\"/\"${directory}\":/\"${directory}\""
    done

    echo "For mysql_init container"
    echo "========================"
    echo "  environment:"
    echo '    MARIADB_ROOT_PASSWORD: "${MARIADB_ROOT_PASSWORD}"'
    echo '    LOCAL_BASE_DIRECTORY: "${LOCAL_BASE_DIRECTORY}"'
    echo '    CONTAINER_BASE_DIRECTORY: "${CONTAINER_BASE_DIRECTORY}"'
    echo '    MYSQL_BASE_DIRECTORY: "${MYSQL_BASE_DIRECTORY}"'
    echo '    MOUNTS_DIRECTORY: "${MOUNTS_DIRECTORY}"'
    echo '    SHARED_DIRECTORY: "${SHARED_DIRECTORY}"'
    echo '    DONE_FILE_NAME: "${DONE_FILE_NAME}"'
    echo '    MYSQL_DIRECTORIES: "${MYSQL_DIRECTORIES}"'

    echo "  volumes:"
    # shellcheck disable=SC2089
    MYSQL_REMOTE_BASE='"${CONTAINER_BASE_DIRECTORY}"/"${MYSQL_BASE_DIRECTORY}"'
    for directory in ${MYSQL_DIRECTORIES//#/ /}; do
        echo "    - \"${MYSQL_LOCAL_BASE}/${directory}\":\"${MYSQL_REMOTE_BASE}/${directory}\""
    done
    echo "    - \"${SHARED_LOCAL_BASE}\":\"${CONTAINER_BASE_DIRECTORY}/${SHARED_DIRECTORY}\""
    set +x
}

function run_init(){
    # shellcheck disable=SC2162
    read -p "If you want to remove all stored data, type REMOVE: "
    if [ "$REPLY" != "REMOVE" ]; then
        return 1
    fi

    recreate_directories
    echo "Make sure the following folders are mounted appropriately, and the following variables set:"
    output_mysql_data

    echo ""
}


if [ "${DEBUG}" == "true" ]; then
    report_values
fi

case "${1}" in
    init)
        run_init
    ;;
    ps)
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" ps
    ;;
    start)
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" start
    ;;
    stop)
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" stop
    ;;
    up)
        if [ -z "${MARIADB_ROOT_PASSWORD}" ]; then
            read -s -r -p "MARIADB_ROOT_PASSWORD: " MARIADB_ROOT_PASSWORD
            echo ""
        fi

        export MARIADB_ROOT_PASSWORD
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" up --remove-orphans
    ;;
    down)
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" down
    ;;
    logs)
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" logs "${2}"
    ;;
    exec)
        # shellcheck disable=SC2086,SC2068
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" exec -ti "${@:2}"
    ;;
    restart)
        # shellcheck disable=SC2086
        docker compose -f "${BE_COMPOSE_FILE_FULLPATH}" restart ${2:-}
    ;;
    reset)
        RESET=true $0 start
    ;;
    *)
        echo "Invalid option ${1}"
    ;;
esac

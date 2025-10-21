           

                                                                                                                                                                                                                  



set -euo pipefail



SANDBOX_DIR=$(jq -r '.sandbox_dir' config/permissions.json)             

ACTION=$1                   

TARGET=$2                               

SIMULATE=${3:-false}                 



if [[ ! $TARGET = $SANDBOX_DIR* ]]; then

  echo "Error: Target $TARGET outside sandbox $SANDBOX_DIR" >&2

  exit 1

fi



if [[ $SIMULATE == "true" ]]; then

  echo "Simulate: Would $ACTION $TARGET"

  exit 0

fi



case $ACTION in

  read_file)

    bwrap --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind "$SANDBOX_DIR" /sandbox --chdir /sandbox cat "${TARGET#$SANDBOX_DIR/}"

    ;;

  modify_file)

    echo "Modified content" | bwrap --bind "$SANDBOX_DIR" /sandbox --chdir /sandbox tee "${TARGET#$SANDBOX_DIR/}" >/dev/null

    ;;

  *)

    echo "Unsupported action: $ACTION" >&2

    exit 1

    ;;

esac

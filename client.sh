if [[ $# -ne 2 ]]; then
    echo "Usage: ./client.sh <id> <configuration path>"
    exit 100
elif [[ ! -f $2 ]]; then # config file does not exist
    echo "Could not find a valid configuration file at precised path."
    exit 200
fi

while IFS= read -r line; do
    array=( $line )
    group="${array[0]}"
    if [[ $group = "acceptors" ]]; then
        acceptors=(${array[@]})
    elif [[ $group = "clients" ]]; then
        clients=(${array[@]})
    elif [[ $group = "learners" ]]; then
        learners=(${array[@]})
    elif [[ $group = "proposers" ]]; then
        proposers=(${array[@]})
    fi
done < "$2"

python3 client.py "$1" "${clients[1]}" "${clients[2]}" "${proposers[1]}" "${proposers[2]}"
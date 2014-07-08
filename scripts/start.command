current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/start.sh" ]; then
    source "$current_dir/start.sh" $1
else
    source "$current_dir/scripts/start.sh" $1
fi
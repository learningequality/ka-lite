current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/stop.sh" ]; then
    source "$current_dir/stop.sh"
else
    source "$current_dir/scripts/stop.sh"
fi
current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/start.sh" ]; then
    source "$current_dir/start.sh"
else
    source "$current_dir/scripts/start.sh"
fi
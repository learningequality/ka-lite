current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/run_command.sh" ]; then
    source "$current_dir/run_command.sh"
else
    source "$current_dir/scripts/run_command.sh"
fi
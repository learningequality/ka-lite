cd `dirname "${BASH_SOURCE[0]}"`
python manage.py graph_models securesync main -g -o model_graph.png
eog model_graph.png
rm model_graph.png

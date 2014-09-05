import csv 
import StringIO
from tastypie.exceptions import NotFound
from tastypie.serializers import Serializer 


class CSVSerializer(Serializer):
    formats = ['json', 'csv']
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
    }

    def to_csv(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        raw_data = StringIO.StringIO()

        objects = data.get("objects")

        if not objects:
            raise NotFound("No objects provided for serialization")

        header = objects[0].keys()
        writer = csv.writer(raw_data, header)
        writer.writerow(header)

        for item in objects:
            writer.writerow(item.values())

        raw_data.seek(0)
        return raw_data.read()

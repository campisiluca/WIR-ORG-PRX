import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
import csv
import os

output_folder = 'output'
xes_file_path = 'running-example.xes'
csv_file_path = os.path.join(output_folder, 'output_file.csv')

log = xes_importer.apply(xes_file_path)

unique_attributes = set()
for case in log:
    for event in case:
        unique_attributes.update(event.keys())
# Entfernen von Standardattributen
standard_attributes = {'concept:name', 'time:timestamp', 'org:resource'}
unique_attributes -= standard_attributes

header = ['Case ID', 'Activity', 'Timestamp', 'Resource']
header.extend(unique_attributes)

with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(header)

    for case in log:
        case_id = case.attributes['concept:name']
        for event in case:
            row = [
                case_id,
                event['concept:name'],
                event['time:timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                event.get('org:resource', '')
            ]
            for attr in unique_attributes:
                row.append(event.get(attr, ''))
            writer.writerow(row)

print(f"XES-Log wurde erfolgreich in {csv_file_path} konvertiert.")

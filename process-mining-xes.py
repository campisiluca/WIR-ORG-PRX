import os
import pm4py
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization
from pm4py.streaming.stream.live_event_stream import LiveEventStream
from pm4py.streaming.algo.conformance.tbr import algorithm as tbr_algorithm
from pm4py.statistics.attributes.log import get as attributes_get
from pm4py.visualization.performance_spectrum import visualizer as ps_visualizer
from pm4py.algo.discovery.performance_spectrum import algorithm as performance_spectrum
from pm4py.statistics.traces.generic.log import case_arrival
from pm4py.objects.log.util import interval_lifecycle



from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from xml.etree import ElementTree

# Pfad zur XES-Datei
xes_file_path = 'running-example.xes'

# Sammeln aller einzigartigen Aktivitäten aus dem Ereignisprotokoll
unique_activities = set()
with open(xes_file_path, 'r') as file:
    for line in file:
        if 'key="Activity"' in line and 'value="string"' not in line:
            activity = line.split('value="')[1].split('"')[0]
            unique_activities.add(activity)

# Umwandlung des Sets in eine Liste
unique_activities_list = list(unique_activities)
print(unique_activities_list)

# Importieren des Ereignisprotokolls aus einer XES-Datei
log = xes_importer.apply(xes_file_path)

# Überprüfen, ob der Ausgabeordner existiert, und erstellen Sie ihn, falls nicht
output_folder = 'output/xes'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Anwenden des Inductive Miners, um ein BPMN-Modell zu erzeugen
process_model = pm4py.discover_bpmn_inductive(log)

# Speichern des BPMN-Modells als PNG-Bild
bpmn_graph = bpmn_visualizer.apply(process_model)
bpmn_file_path = os.path.join(output_folder, 'process_model_bpmn.png')
bpmn_visualizer.save(bpmn_graph, bpmn_file_path)

# Anwenden des Alpha Miner, um ein Petri-Netz-Prozessmodell zu extrahieren
net, initial_marking, final_marking = alpha_miner.apply(log)

# Speichern des Petri-Netz-Prozessmodells als Bild
gviz_petri = pn_visualizer.apply(net, initial_marking, final_marking)
petri_file_path = os.path.join(output_folder, 'process_model_petri.png')
pn_visualizer.save(gviz_petri, petri_file_path)

# Anwenden des Inductive Miners, um einen Prozessbaum zu erzeugen
process_tree = pm4py.discover_process_tree_inductive(log)

# Visualisieren und Speichern des Prozessbaums als PNG-Bild
gviz_pt = pt_visualizer.apply(process_tree)
pt_file_path = os.path.join(output_folder, 'process_tree.png')
pt_visualizer.save(gviz_pt, pt_file_path)

# Entdecken des Direkt-Folge-Graphen aus dem Log
dfg = dfg_discovery.apply(log)

# Visualisieren des Direkt-Folge-Graphen
gviz_dfg = dfg_visualization.apply(dfg, log=log, variant=dfg_visualization.Variants.FREQUENCY)
dfg_file_path = os.path.join(output_folder, 'directly_follows_graph.png')
dfg_visualization.save(gviz_dfg, dfg_file_path)

# Berechnen der Zeit zwischen aufeinanderfolgenden Aktivitäten
activity_durations = defaultdict(list)
for trace in log:
    for i in range(1, len(trace)):
        prev_event = trace[i - 1]
        curr_event = trace[i]
        prev_time = prev_event["time:timestamp"]
        curr_time = curr_event["time:timestamp"]
        duration = (curr_time - prev_time).total_seconds()
        activity_durations[curr_event["concept:name"]].append(duration)

# Berechnen der Durchschnittszeiten für jede Aktivität
avg_activity_durations = {act: np.mean(durs) for act, durs in activity_durations.items()}

# Erstellen eines DataFrames aus den berechneten Zeiten
df_avg_durations = pd.DataFrame(list(avg_activity_durations.items()), columns=['Activity', 'Average Duration'])

# Sortieren der Daten für eine bessere Visualisierung
df_avg_durations = df_avg_durations.sort_values(by='Average Duration')

# Erstellen eines Balkendiagramms
plt.figure(figsize=(10, 6))
plt.barh(df_avg_durations['Activity'], df_avg_durations['Average Duration'])
plt.xlabel('Durchschnittsdauer zwischen Aktivitäten (in Sekunden)')
plt.ylabel('Aktivitäten')
plt.title('Durchschnittsdauer zwischen Aktivitäten')

# Speichern des Diagramms als PNG-Datei
output_file_path = os.path.join(output_folder, 'average_duration_between_activities.png')
plt.savefig(output_file_path)

print(f"Diagramm gespeichert als: {output_file_path}")

# Berechnen der Durchsatzzeiten für jeden Fall
all_case_durations = pm4py.get_all_case_durations(log)

# Erstellen eines Histogramms der Durchsatzzeiten
plt.figure(figsize=(10, 6))
plt.hist(all_case_durations, bins=30, color='blue', edgecolor='black')
plt.xlabel('Durchsatzzeit (in Sekunden)')
plt.ylabel('Anzahl der Fälle')
plt.title('Verteilung der Durchsatzzeiten')

# Speichern des Diagramms als PNG-Datei
output_file_path = os.path.join(output_folder, 'throughput_time_distribution.png')
plt.savefig(output_file_path)

print(f"Diagramm gespeichert als: {output_file_path}")

# Berechnen des Case Arrival Ratios
case_arrival_ratio = pm4py.get_case_arrival_average(log)

# Berechnen des Case Dispersion Ratios
case_dispersion_ratio = case_arrival.get_case_dispersion_avg(log, parameters={
    case_arrival.Parameters.TIMESTAMP_KEY: "time:timestamp"})

# Erstellen eines Balkendiagramms für Case Arrival/Dispersion Ratio
plt.figure(figsize=(6, 4))
plt.bar(['Case Arrival Ratio', 'Case Dispersion Ratio'], [case_arrival_ratio, case_dispersion_ratio], color=['blue', 'green'])
plt.ylabel('Durchschnittliche Zeit (in Sekunden)')
plt.title('Case Arrival/Dispersion Ratio')

# Speichern des Diagramms als PNG-Datei
output_file_path = os.path.join(output_folder, 'case_arrival_dispersion_ratio.png')
plt.savefig(output_file_path)

# Umwandeln des Logs in ein "interval" Log für Cycle Time und Waiting Time
interval_log = interval_lifecycle.assign_lead_cycle_time(log)

# Berechnen von Cycle Time und Waiting Time
cycle_times = []
waiting_times = []
for case in interval_log:
    for event in case:
        cycle_time = event.get("@@approx_bh_partial_cycle_time", 0)
        waiting_time = event.get("@@approx_bh_this_wasted_time", 0)
        cycle_times.append(cycle_time)
        waiting_times.append(waiting_time)

# Erstellen von Histogrammen für Cycle Time und Waiting Time
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.hist(cycle_times, bins=30, color='blue', edgecolor='black')
plt.xlabel('Cycle Time (in Sekunden)')
plt.ylabel('Anzahl der Ereignisse')
plt.title('Cycle Time Verteilung')

plt.subplot(1, 2, 2)
plt.hist(waiting_times, bins=30, color='green', edgecolor='black')
plt.xlabel('Waiting Time (in Sekunden)')
plt.ylabel('Anzahl der Ereignisse')
plt.title('Waiting Time Verteilung')


# Speichern des Diagramms als PNG-Datei
output_file_path = os.path.join(output_folder, 'cycle_waiting_time_distribution.png')
plt.savefig(output_file_path)

# Optional: Diagramm anzeigen
plt.show()

print(f"Diagramm gespeichert als: {output_file_path}")

# Konvertieren des Logs in ein Event-Log (falls erforderlich)
logevent = pm4py.convert_to_event_log(log)
activities = ["register request", "examine casually", "check ticket", "decide"]

# Berechnen des Performance Spectrum
perf_spectrum = performance_spectrum.apply(logevent, activities)

# Visualisieren des Performance Spectrum
gviz = ps_visualizer.apply(perf_spectrum)

# Speichern des Performance Spectrum als PNG-Datei
output_file_path = os.path.join(output_folder, 'performance_spectrum.png')
ps_visualizer.save(gviz, output_file_path)

print(f"Performance Spectrum gespeichert als: {output_file_path}")
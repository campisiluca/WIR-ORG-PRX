import os
import pm4py
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.util import dataframe_utils
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization
from pm4py.statistics.traces.generic.log import case_arrival
from pm4py.objects.log.util import interval_lifecycle
from pm4py.visualization.performance_spectrum import visualizer as ps_visualizer
from pm4py.algo.discovery.performance_spectrum import algorithm as performance_spectrum
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

# Pfad zur CSV-Datei
csv_file_path = 'output/output_file.csv'

# Lesen der CSV-Datei
df = pd.read_csv(csv_file_path)

# Umbenennen der Spaltennamen für PM4Py
df.rename(columns={'Case ID': 'case:concept:name', 'Activity': 'concept:name', 'Timestamp': 'time:timestamp'}, inplace=True)

# Konvertieren der Zeitstempelspalte in das richtige Format
df['time:timestamp'] = pd.to_datetime(df['time:timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

log = log_converter.apply(df)

# Überprüfen, ob der Ausgabeordner existiert, und erstellen Sie ihn, falls nicht
output_folder = 'output/csv'
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


print("Alle Analysen wurden erfolgreich durchgeführt und gespeichert.")
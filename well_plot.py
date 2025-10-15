from PyQt5.QtWidgets import QDialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

class CurvePlotSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select variables for curve plots")
        self.setGeometry(200, 200, 300, 100)

class SeriesPlotSettings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select variables for series plots")
        self.setGeometry(200, 200, 300, 100)

class ConcentrationPlotSettings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select variables for concentration plots")
        self.setGeometry(200, 200, 300, 100)

class LithologyPlotSettings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select variables for lithology plots")
        self.setGeometry(200, 200, 300, 100)

class UpdatePlot(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select plots order")
        self.setGeometry(200, 200, 300, 100)

# # Load and clean data
# df = pd.read_csv("data/Dataset_unificado_T2.csv", sep=";", low_memory=False)

# # Convert comma decimals to dots and numeric
# for col in df.columns[1:]:
#     df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
#     df[col] = pd.to_numeric(df[col], errors="coerce")

# # Extract numeric part of the time columns
# time_cols = df.columns[7:37]
# times = time_cols.to_series().str.extract(r'([\d\.eE+-]+)').astype(float)[0].values

# # Select one well (first one)
# well = df['Well Name'].unique()[0]
# well_df = df.loc[df['Well Name'] == well, :]

# # Get depths and corresponding NMR amplitudes
# depths = well_df['TVD'].values
# data = well_df.iloc[:, 7:37].values  # shape = (n_depths, n_times)

# # Sort depths in ascending order (optional, good for visualization)
# sort_idx = np.argsort(depths)
# depths = depths[sort_idx]
# data = data[sort_idx, :]

# # Logs to plot
# log_cols = [
#     "Sonic/DTC",
#     "Resistivity/Deep",
#     "Spectral Gamma Ray/U",
#     "Spectral Gamma Ray/TH",
#     "Spectral Gamma Ray/K (Spec)",
#     "Gamma Ray",
#     "Density",
#     "Photoelectric Factor",
#     "Lithogeochemical/Ca",
#     "Lithogeochemical/Si",
#     "Lithogeochemical/Fe",
#     "Lithogeochemical/Al",
#     "Lithogeochemical/Ti",
#     "Lithogeochemical/S",
#     "Lithogeochemical/FY2W",
#     "Neutron/Thermal Porosity"
# ]

# # Plot as a 2D color map
# n_logs = len(log_cols)
# fig = plt.figure(figsize=(2+n_logs*1.5, 8))
# gs = GridSpec(1, n_logs+1, width_ratios=[3] + [1]*n_logs, wspace=0.1)

# # Time series log
# ax0 = fig.add_subplot(gs[0,0])
# pcm = ax0.pcolormesh(times, depths, data, shading='auto', cmap='viridis')
# ax0.set_xscale('log')
# ax0.set_xlabel('Time (s)')
# ax0.set_ylabel('Depth (m)')
# ax0.invert_yaxis()
# cbar = plt.colorbar(pcm,ax=ax0,pad=0.01)
# cbar.set_label('Amplitude')

# # Well logs
# for i, col in enumerate(log_cols):
#     ax = fig.add_subplot(gs[0, i+1], sharey=ax0)
#     log_data = well_df[col].values[sort_idx]
    
#     ax.plot(log_data, depths, color="black", linewidth=0.8)
#     ax.set_xlabel(col.split("/")[-1], fontsize=6)  # shorter label
#     ax.invert_yaxis()
#     ax.grid(True, linestyle=":", alpha=0.4)
#     ax.set_yticklabels([])  # only leftmost has depth labels
    
#     # Optional: auto limits with small padding
#     finite_data = log_data[np.isfinite(log_data)]
#     if len(finite_data) > 0:
#         xmin, xmax = np.nanpercentile(finite_data, [2, 98])
#         ax.set_xlim(xmin, xmax)
    
#     ax.set_title(col, fontsize=6, pad=4)

# plt.tight_layout()
# plt.show()
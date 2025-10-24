import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# # Extract numeric part of the time columns
# time_cols = df.columns[7:37]
# times = time_cols.to_series().str.extract(r'([\d\.eE+-]+)').astype(float)[0].values

# # Select one well (first one)
# well_idx = 0
# well = df['Well Name'].unique()[well_idx]
# well_df = df.loc[df['Well Name'] == well, :]

# # Get depths and corresponding NMR amplitudes
# depths = well_df['TVD'].values
# data = well_df.iloc[:, 7:37].values  # shape = (n_depths, n_times)

# # Sort depths in ascending order (optional, good for visualization)
# sort_idx = np.argsort(depths)
# depths = depths[sort_idx]
# data = data[sort_idx, :]
# depth_min, depth_max = np.nanmin(depths), np.nanmax(depths)

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
# gs = GridSpec(2, n_logs+2, width_ratios=[3]+[3]+[2]*n_logs, height_ratios=[30,1], wspace=0.5, hspace=0.2)

# # -------------------------------------------- Time series log
# ax0 = fig.add_subplot(gs[0,0])
# pcm = ax0.pcolormesh(times, depths, data, shading='auto', cmap='viridis')
# ax0.set_xscale('log')
# ax0.set_xlabel('Time (s)')
# ax0.set_ylim(depth_max, depth_min)
# ax0.set_ylabel('Depth (m)')
# ax0.invert_yaxis()
# ax00 = fig.add_subplot(gs[1,0])
# cbar = plt.colorbar(pcm, cax=ax00, orientation='horizontal', pad=0.15, fraction=0.05)
# cbar.set_label('Amplitude')

# # -------------------------------------------- Proportion plot
# prop_cols = ["Lithogeochemical/Ca", "Lithogeochemical/Si", "Lithogeochemical/Fe"]
# well_df["sum_elements"] = well_df[prop_cols].sum(axis=1)
# for col in prop_cols:
#     well_df[f"{col}_prop"] = well_df[col] / well_df["sum_elements"]
# #
# well_df = well_df.sort_values("TVD").reset_index(drop=True)
# depths = well_df["TVD"].values
# #
# ax1 = fig.add_subplot(gs[0,1], sharey=ax0)
# colors = {
#     "Lithogeochemical/Ca_prop": "lightblue",
#     "Lithogeochemical/Si_prop": "gold",
#     "Lithogeochemical/Fe_prop": "darkred"
# }
# bottom = np.zeros(len(well_df))
# # Plot stacked horizontal bars
# for col, color in colors.items():
#     ax1.barh(depths, well_df[col], left=bottom, color=color, label=col.split('/')[-2])
#     bottom += well_df[col].values
# # Formatting
# # ax1.set_xlabel("Proportion")
# # ax1.invert_yaxis()  # Depth increases downward
# ax1.set_xlim(0, 1)
# ax1.set_ylim(depth_max, depth_min)
# ax1.set_yticklabels([])  # only leftmost has depth labels
# # Create a dedicated legend axis below (gs[1,1])
# ax1_leg = fig.add_subplot(gs[1, 1])
# ax1_leg.axis("off")  # hide axes
# handles, labels = ax1.get_legend_handles_labels()
# ax1_leg.legend(handles, labels, title="", loc="center", ncol=1, frameon=False)

# # -------------------------------------------- Well logs
# for i, col in enumerate(log_cols):
#     ax = fig.add_subplot(gs[0, i+2], sharey=ax0)
#     log_data = well_df[col].values[sort_idx]
    
#     ax.plot(log_data, depths, color="black", linewidth=0.8)
#     ax.set_xlabel(col.split("/")[-1], fontsize=6)  # shorter label
#     # ax.invert_yaxis()
#     ax.grid(True, linestyle=":", alpha=0.4)
#     ax.set_yticklabels([])  # only leftmost has depth labels
#     ax.set_ylim(depth_max, depth_min)
    
#     # Optional: auto limits with small padding
#     finite_data = log_data[np.isfinite(log_data)]
#     if len(finite_data) > 0:
#         xmin, xmax = np.nanpercentile(finite_data, [2, 98])
#         ax.set_xlim(xmin, xmax)
    
#     ax.set_title(col, fontsize=6, pad=4)

# plt.title(f"Well Name: {df['Well Name'].unique()[well_idx]}", pad=15)
# # plt.tight_layout()
# plt.show()

# 1) Load and clean data and convert comma decimals to dots and numeric (this can be accessed through the variable self.df)
df = pd.read_csv("data/Dataset_unificado_T2.csv", sep=";", low_memory=False)
for col in df.columns[1:]:
    df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
    df[col] = pd.to_numeric(df[col], errors="coerce")
# 2) Select the current well in the combo box that will be automatically plotted in the figure canvas
well_idx = 10 # there are 50 wells in the dataset
current_well = df['Well Name'].unique()[well_idx]
# 3) Get the add plot and gridspec settings button parameters from the GUI (these are just example parameters, the real ones will come from the GUI)
selected_params = {
    'curves': [
        {'variable': 'Sonic/DTC', 'name': 'Sonic/DTC', 'color': '#000000', 'unit': ''}, 
        {'variable': 'Spontaneous Potential/SP', 'name': 'Spontaneous Potential/SP', 'color': '#000000', 'unit': ''}, 
        {'variable': 'Gamma Ray', 'name': 'Gamma Ray', 'color': '#000000', 'unit': ''}], 
    'time series': [
        {'start_col': '0.0005s', 'end_col': '3s', 'name': 'NMR', 'colormap': 'viridis', 'logscale': True, 'unit': ''}], 
    'proportions': [
        {'name': 'Ca-Si-Fe', 'variable_list': ['Lithogeochemical/Ca', 'Lithogeochemical/Si', 'Lithogeochemical/Fe'], 'color_list': ['#00ffff', '#ffff00', '#aa0000'], 'label_list': ['Ca', 'Si', 'Fe']}]}
gridspec_params = {
    'orders': {
        'curves': ['Sonic/DTC', 'Spontaneous Potential/SP', 'Gamma Ray'], 
        'time series': ['NMR'], 
        'proportions': ['Ca-Si-Fe']}, # ignore this parameter for now
    'gridspec': {'width_ratios': [2.0, 3.0, 5.0], 'height_ratios': [30.0, 1.0], 'wspace': 0.5, 'hspace': 0.2}}

def plot_func(df, current_well, selected_params, gridspec_params):
    # Get well dataframe and its depths
    well_df = df.loc[df['Well Name'] == current_well, :]
    depths = well_df['TVD'].values # get parameters function (after loading the csv) will return the name of the column with depths
    depth_max = np.nanmax(depths)
    depth_min = np.nanmin(depths)
    n_curves = len(selected_params['curves'])
    n_series = len(selected_params['time series'])
    n_proportions = len(selected_params['proportions'])
    n_cols = n_curves + n_series + n_proportions

    # Set the figure and gridspec
    fig = plt.figure(figsize=(2+n_cols*1.5, 8)) # let the user decide the figsize and set it as gridspec_params?
    width_ratios = []
    for w, i in zip(gridspec_params['gridspec']['width_ratios'], [n_curves, n_series, n_proportions]):
        width_ratios += [w] * i
    gs = GridSpec(2, n_cols, width_ratios=width_ratios, height_ratios=gridspec_params['gridspec']['height_ratios'], wspace=gridspec_params['gridspec']['wspace'], hspace=gridspec_params['gridspec']['hspace'])

    # Plot curves first
    if n_curves > 0:
        for i, curve in enumerate(selected_params['curves']):
            ax = fig.add_subplot(gs[0, i])
            curve_data = well_df[curve['variable']].values
            ax.plot(curve_data, depths, color=curve['color'], linewidth=0.8)
            ax.set_xlabel(curve['unit'], fontsize=6)  # shorter label
            ax.grid(True, linestyle=":", alpha=0.4)
            if i == 0:
                ax.set_ylabel('Depth (m)')
            else:
                ax.set_yticklabels([])
            ax.set_ylim(depth_max, depth_min)
            finite_data = curve_data[np.isfinite(curve_data)]
            if len(finite_data) > 0:
                xmin, xmax = np.nanpercentile(finite_data, [2, 98])
                ax.set_xlim(xmin, xmax)
            ax.set_title(curve['name'], fontsize=6, pad=4)

    # Plot time series
    if n_series > 0:
        for i, series in enumerate(selected_params['time series']):
            # Extract numeric part of the time columns
            time_cols = well_df.loc[:, series['start_col']:series['end_col']].columns
            times = time_cols.to_series().str.extract(r'([\d\.eE+-]+)').astype(float)[0].values
            data = well_df.loc[:, series['start_col']:series['end_col']].values  # shape = (n_depths, n_times)
            ax = fig.add_subplot(gs[0, n_curves + i])
            pcm = ax.pcolormesh(times, depths, data, shading='auto', cmap=series['colormap'])
            if series['logscale']:
                ax.set_xscale('log')
            ax.set_xlabel(f'Time')
            ax.set_ylim(depth_max, depth_min)
            ax.set_title(series['name'], fontsize=6, pad=4)
            ax0 = fig.add_subplot(gs[1, n_curves + i])
            cbar = plt.colorbar(pcm, cax=ax0, orientation='horizontal', pad=0.15, fraction=0.05)
            # cbar.set_label('Amplitude')

    # Plot proportions
    if n_proportions > 0:
        for i, prop in enumerate(selected_params['proportions']):
            # Calculate proportions
            well_df["sum_elements"] = well_df[prop['variable_list']].sum(axis=1)
            for var in prop['variable_list']:
                well_df[f"{var}_prop"] = well_df[var] / well_df["sum_elements"]
            well_df = well_df.sort_values("TVD").reset_index(drop=True)
            depths = well_df["TVD"].values
            ax = fig.add_subplot(gs[0, n_curves + n_series + i], sharey=ax if (n_curves + n_series + i) > 0 else None)
            bottom = np.zeros(len(well_df))
            for var, color, label in zip(prop['variable_list'], prop['color_list'], prop['label_list']):
                ax.barh(depths, well_df[f"{var}_prop"], left=bottom, color=color, label=label)
                bottom += well_df[f"{var}_prop"].values
            ax.set_xlim(0, 1)
            ax.set_ylim(depth_max, depth_min)
            if (n_curves + n_series + i) > 0:
                ax.set_yticklabels([])  # only leftmost has depth labels
            ax.set_title(prop['name'], fontsize=6, pad=4)
            # Create a dedicated legend axis below
            ax_leg = fig.add_subplot(gs[1, n_curves + n_series + i])
            ax_leg.axis("off")  # hide axes
            handles, labels = ax.get_legend_handles_labels()
            ax_leg.legend(handles, labels, title="", loc="center", ncol=1, frameon=False)

    # Finish the plot
    # plt.title(f"Well Name: {current_well}")
    plt.show()

plot_func(df, current_well, selected_params, gridspec_params)
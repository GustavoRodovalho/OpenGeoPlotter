import pandas as pd
import mplcursors
import seaborn as sns
import matplotlib.pyplot as plt

def plot_variable_statistics(self):
    if self.df is None:
        return

    self.canvas.figure.clf()
    ax = self.canvas.figure.add_subplot(111)

    numeric_df = self.df.select_dtypes(include=["number"]).dropna()
    melted = numeric_df.melt(var_name="Variable", value_name="Value")

    sns.boxplot(x="Variable", y="Value", data=melted, ax=ax, showfliers=False)
    strip = sns.stripplot(x="Variable", y="Value", data=melted, ax=ax, color="black", alpha=0.3, jitter=True)

    ax.set_title("Variable Statistics")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

    # Add hover tooltips
    mplcursors.cursor(strip.collections, hover=True)

    self.canvas.draw()
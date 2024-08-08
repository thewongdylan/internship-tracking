# Imports
import pandas as pd
import numpy as np
from decouple import config
import plotly.graph_objects as go
from datetime import datetime

pd.options.mode.chained_assignment = None  # default='warn'

def connect_to_gsheets() -> pd.DataFrame:
    """Connect to Google Sheets and retrieve data
    
    Returns: raw DataFrame
    """

    sheet_id = config("SHEET_ID")
    sheet_name = "Applications"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    if pd.read_csv(sheet_url).empty:
        raise ValueError("No data found in Google Sheets")
    
    applications_raw = pd.read_csv(sheet_url)

    return applications_raw

def clean_data(applications_raw) -> pd.DataFrame:
    """Basic cleaning of data
    - Drop columns with all NaN values
    - Drop columns that are not needed
    - Drop rows with all NaN values

    Returns: cleaned DataFrame
    """

    applications = applications_raw.dropna(how='all', axis=1)
    applications.drop(columns=['S/N', 'Company', 'Position', 'Date Applied', 'Link'], inplace=True)
    applications.dropna(how='all', axis=0, inplace=True)

    return applications

def get_unique_values(applications) -> dict:
    """Get unique values for various phases of the application process
    - job_sources: unique sources of job postings
    - statuses: unique statuses
    - intermediate_statuses: unique statuses excluding 'Rejected', 'DNF', 'Offered', 'Accepted'
    - unique_nodes: unique nodes for the sankey diagram
    - node_value_counts: counts of each node
    - unique_nodes_with_values: unique nodes with their counts

    Returns: dictionary of unique values
    """

    # Lists of unique values for various phases
    job_sources = applications['Source'].unique().tolist()

    status_stages = [stage for stage in applications.columns if stage.startswith('Status')]
    for i in range(len(status_stages)):
        if i == 0:
            statuses = applications[status_stages[i]].unique().tolist()
        else:
            statuses.extend(applications[status_stages[i]].unique().tolist())
    statuses = list(set(statuses))
    statuses.remove(np.nan)

    intermediate_statuses = statuses.copy()
    to_remove = ['Rejected after Applying', 'Rejected after Interview', 'Rejected', 'DNF', 'Offered', 'Accepted', 'Declined']
    for item in to_remove:
        if item in intermediate_statuses:
            intermediate_statuses.remove(item)

    unique_nodes = ['Applications', 'No reply']
    unique_nodes += job_sources + statuses

    node_value_counts = {node: 0 for node in unique_nodes}
    job_sources_count = applications['Source'].value_counts().to_dict()
    for source in job_sources_count:
        node_value_counts[source] += job_sources_count[source]
    for stage in status_stages: 
        status_count = applications[stage].value_counts().to_dict()
        for status in status_count:
            node_value_counts[status] += status_count[status]
    node_value_counts['Applications'] = len(applications)
    node_value_counts['No reply'] = len(applications[applications['Status 1'].isna() & applications['Status 2'].isna()])

    unique_nodes_with_values = [node + ': ' + str(node_value_counts[node]) for node in node_value_counts]

    unique_values_dict = {
        'job_sources': job_sources,
        'statuses': statuses,
        'intermediate_statuses': intermediate_statuses,
        'unique_nodes': unique_nodes,
        'node_value_counts': node_value_counts,
        'unique_nodes_with_values': unique_nodes_with_values
    }

    return unique_values_dict, status_stages

def generate_sankey_df(applications, status_stages) -> pd.DataFrame:
    """Generate DataFrame for plotly to plot a Sankey Diagram
    The dataframe requires 3 columns: source, target, value
    At this point, the data is still in human-readable format

    Returns: DataFrame for Sankey Diagram
    """

    # Make df for sankey graph
    sankey_df = pd.DataFrame(columns=['source', 'target', 'value'])

    # Applications -> Source
    application_sources = applications['Source'].value_counts()
    for application_source in application_sources.index:
        source = application_source
        value = application_sources[application_source]
        sankey_df = sankey_df._append({'source': 'Applications', 'target': source, 'value': value}, ignore_index=True)

    # Source -> Status 1
    application_statuses_1 = {}
    for index, row in applications.iterrows():
        if pd.notna(row['Status 1']):
            status_update_1 = row['Source'], row['Status 1']
            if status_update_1 in application_statuses_1:
                application_statuses_1[status_update_1] += 1
            else:
                application_statuses_1[status_update_1] = 1
        else:
            no_update_status = row['Source'], 'No reply'
            if no_update_status in application_statuses_1:
                application_statuses_1[no_update_status] += 1
            else:
                application_statuses_1[no_update_status] = 1

    for status_update_1 in application_statuses_1:
        sankey_df = sankey_df._append({'source': status_update_1[0], 'target': status_update_1[1], 'value': application_statuses_1[status_update_1]}, ignore_index=True)

    # Status 1 -> Status N
    for i in range(len(status_stages)):
        if i != 0:
            application_statuses_i = {}
            for index, row in applications.iterrows():
                if pd.notna(row[status_stages[i]]):
                    flow = row[status_stages[i-1]], row[status_stages[i]]
                    if flow in application_statuses_i:
                        application_statuses_i[flow] += 1
                    else:
                        application_statuses_i[flow] = 1
            
            for flow in application_statuses_i:
                sankey_df = sankey_df._append({'source': flow[0], 'target': flow[1], 'value': application_statuses_i[flow]}, ignore_index=True)

    return sankey_df

def generate_color_references(unique_values_dict, sankey_df) -> dict:
    """Generate color references for nodes and links
    - node_colors: list of colors for each node
    - link_colors: list of colors for each link

    Link colors are based on the target node with reduced opacity
    
    Returns: dictionary of colors
    """

    # Load unique values
    job_sources = unique_values_dict['job_sources']
    intermediate_statuses = unique_values_dict['intermediate_statuses']
    unique_nodes = unique_values_dict['unique_nodes']

    # Define variables for colors for easier modification
    node_blue = 'rgba(39, 125, 161, 1)'
    node_yellow = 'rgba(249, 199, 79, 1)'
    node_grey = 'rgba(173, 181, 189, 1)'
    node_red = 'rgba(249, 65, 68, 1)'
    node_green = 'rgba(67, 170, 139, 1)'
    node_black = 'rgba(0, 0, 0, 1)'
    link_blue = node_blue.replace('1)', '0.5)')
    link_yellow = node_yellow.replace('1)', '0.5)')
    link_grey = node_grey.replace('1)', '0.5)')
    link_red = node_red.replace('1)', '0.5)')
    link_green = node_green.replace('1)', '0.5)')
    link_black = node_black.replace('1)', '0.5)')

    node_colors = ['rgba(39, 125, 161, 1)'] # Applications unaccounted for but should already be in list
    for source_target in unique_nodes:
        if source_target in job_sources:
            node_colors.append(node_blue) 
        elif source_target in intermediate_statuses:
            node_colors.append(node_yellow)
        elif source_target == 'No reply':
            node_colors.append(node_grey)
        elif source_target in ['Rejected', 'Rejected after Applying', 'Rejected after Interview']:
            node_colors.append(node_red)
        elif source_target == 'DNF':
            node_colors.append(node_black)
        elif source_target in ['Offered', 'Accepted', 'Declined']:
            node_colors.append(node_green) 

    link_colors = []
    for index, row in sankey_df.iterrows():
        if row['target'] in job_sources:
            link_colors.append(link_blue)
        elif row['target'] in intermediate_statuses:
            link_colors.append(link_yellow)
        elif row['target'] == 'No reply':
            link_colors.append(link_grey)
        elif row['target'] in ['Rejected', 'Rejected after Applying', 'Rejected after Interview']:
            link_colors.append(link_red)
        elif row['target'] == 'DNF':
            link_colors.append(link_black)
        elif row['target'] in ['Offered', 'Accepted', 'Declined']:
            link_colors.append(link_green)

    colors_dict = {
        'node_colors': node_colors,
        'link_colors': link_colors
    }

    return colors_dict

def process_sankey_df(sankey_df, unique_values_dict) -> pd.DataFrame:
    """Process the Sankey DataFrame to assign unique numbers to each source/target
    This is required for the Sankey Diagram to plot correctly

    Returns: processed DataFrame, ready for plotting
    """

    unique_nodes = unique_values_dict['unique_nodes']

    # Assign unique number to each source/target
    mapping_dict = {k: v for v, k in enumerate(unique_nodes)}

    # Map the sources/targets to their unique number
    sankey_df['source'] = sankey_df['source'].map(mapping_dict)
    sankey_df['target'] = sankey_df['target'].map(mapping_dict)

    return sankey_df

def position_nodes(unique_values_dict) -> tuple:
    """Assign positions for each node in the Sankey Diagram
    Unfortunately, hardcoding is required for this step to achieve the desired layout

    Returns: tuple of lists of x and y positions for each node
    """

    unique_nodes = unique_values_dict['unique_nodes']
    job_sources = unique_values_dict['job_sources']

    # Explicitly assigning positions for nodes
    node_pos = {}
    node_pos['Applications'] = (0.1, 0.5)
    for job_source in job_sources:
        node_pos[job_source] = (0.3, 0.1)
    node_pos['Rejected after Applying'] = (0.5, 0.9)
    node_pos['Technical Assessment'] = (0.55, 0.725)
    node_pos['No reply'] = (0.6, 0.35)
    node_pos['On-site Interview'] = (0.65, 0.7)
    node_pos['Online Interview'] = (0.65, 0.75)
    node_pos['DNF'] = (0.625, 0.825)
    node_pos['Rejected after Interview'] = (0.725, 0.8)
    node_pos['Rejected'] = (0.8, 0.925)
    node_pos['Offered'] = (0.8, 0.7)
    node_pos['Declined'] = (0.85, 0.75)
    node_pos['Accepted'] = (0.9, 0.65)

    node_x_pos = [node_pos[node][0] for node in unique_nodes]
    node_y_pos = [node_pos[node][1] for node in unique_nodes]

    return (node_x_pos, node_y_pos)

def plot_sankey(sankey_df, colors_dict, unique_values_dict, node_pos):
    """Plot the Sankey Diagram using Plotly"""

    # Load unique values
    unique_nodes_with_values = unique_values_dict['unique_nodes_with_values']
    node_x_pos, node_y_pos = node_pos

    # Load colors
    node_colors = colors_dict['node_colors']
    link_colors = colors_dict['link_colors']

    # Plot Sankey Diagram
    fig = go.Figure(data=[go.Sankey(
    valueformat = ".0f",
    arrangement = "snap",
    node = dict(
      pad = 20,
      thickness = 10,
      label = unique_nodes_with_values,
      color = node_colors,
      x = node_x_pos,
      y = node_y_pos
    ),
    link = dict(
      source = sankey_df['source'].to_list(),
      target = sankey_df['target'].to_list(),
      value = sankey_df['value'].to_list(),
      color = link_colors
  ))])

    fig.update_layout(title_text="<b>Internship Applications over a 5 month period (Mar - July 2024)<b>", title_xanchor='center', title_x=0.5, title_font_size=22, title_font_family='Helvetica',
                  font_size=14, font_family='Helvetica',
                  annotations=[
                      dict(x=0.5, y =1.07, showarrow=False, text="3rd Year Computer Science and Mathematics Undergraduate", xref="paper", yref="paper"),
                      dict(x=0.5, y=1.04, showarrow=False, text=f"caa {datetime.today().date().strftime('%d %b %Y')}", xref="paper", yref="paper")
                      ],
                  width=1200, height=800)
    fig.show()

    # Export to png
    fig.write_image(f"data/output/Internship Applications Sankey Diagram {datetime.today().date().strftime('%d%m%y')}.png")

def main():
    applications_raw = connect_to_gsheets()
    applications = clean_data(applications_raw)
    unique_values_dict, status_stages = get_unique_values(applications)
    sankey_df = generate_sankey_df(applications, status_stages)
    colors_dict = generate_color_references(unique_values_dict, sankey_df)
    sankey_df = process_sankey_df(sankey_df, unique_values_dict)
    node_pos = position_nodes(unique_values_dict)
    plot_sankey(sankey_df, colors_dict, unique_values_dict, node_pos)

if __name__ == "__main__":
    main()
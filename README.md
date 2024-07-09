# Internship Tracking via Sankey Diagram

![Sample Sankey Diagram](/data/sample/Internship%Applications%Sankey%Diagram%Sample.png "Sample Sankey Diagram")
<p>Here's what the Sankey Diagram looks like!</p>

## Motivation
I've been applying for internships over the past few months, and have been recording all my applications in a Google Sheet.
Seeing this [reddit post](https://www.reddit.com/r/dataisbeautiful/comments/b5sfbh/my_12month_job_search_as_a_recent_graduate_iitn/) inspired me to do something similar, and this repo contains the code I used to generate a similar Sankey Diagram.
- `SankeyGenerator.ipynb`: a Jupyter Notebook used for working purposes, and can be run cell by cell to see how the code works
- TODO: `generate_sankey.py`: a script that runs and automatically generates a Sankey Diagram

## Process
1. Extract data from Google Sheets using `Pandas`
2. Some basic data cleaning and manipulation, all done in `Pandas`
3. Plotting of the Sankey Diagram was done using `Plotly` before exporting

## Dependencies
Install all package requirements as per `requirements.txt`
<br>This can be done via the terminal in your working directory:
```
  pip install -r requirements.txt
```

## Disclaimer
- The code I wrote is specific to the format in which I recorded my internship applications, and is not generally applicable.
- If anything, please feel free to use the code as a guide rather than an exact instruction manual!

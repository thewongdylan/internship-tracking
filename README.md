# Internship Tracking via Sankey Diagram

![Here's what the Sankey Diagram looks like!](/data/sample/Internship%20Applications%20Sankey%20Diagram%20070724.png "Sample Sankey Diagram")


## Motivation
I've been applying for internships over the past few months, and have been recording all my applications in a Google Sheet.
Seeing this [reddit post](https://www.reddit.com/r/dataisbeautiful/comments/b5sfbh/my_12month_job_search_as_a_recent_graduate_iitn/) inspired me to do something similar, and this repo contains the script I used to generate a similar Sankey Diagram.

## Process
1. Extract data from Google Sheets using `Pandas`
2. Some basic data cleaning and manipulation, all done in `Pandas`
3. Plotting of the Sankey Diagram was done using `Plotly` before exporting

## Disclaimer
- The code I wrote is specific to the format in which I recorded my internship applications, and is not generally applicable.
- If anything, please feel free to use the code as a guide rather than an exact instruction manual!
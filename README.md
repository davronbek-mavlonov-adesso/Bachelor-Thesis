# AI Impact on IT Consulting - Survey Dashboard

A local web dashboard to explore and manually classify survey responses about AI impact on IT consulting.

Built with Python, Dash, and Plotly.

## Setup

Requires Python 3.10 or newer: https://www.python.org/downloads/

Open a terminal inside the project folder and run the following commands one by one.

Create a virtual environment (only needed once - this keeps all packages isolated from the rest of your system):

    python -m venv .venv

Install the required packages (only needed once):

Windows:

    .venv\Scripts\python.exe -m pip install -r requirements.txt

Mac / Linux:

    .venv/bin/python -m pip install -r requirements.txt

Start the app:

Windows:

    .venv\Scripts\python.exe app.py

Mac / Linux:

    .venv/bin/python app.py

Then open http://127.0.0.1:8050/ in your browser.
To stop the app, press Ctrl+C in the terminal.

## What it does

- Charts for all 19 survey questions (bar, pie, horizontal bar)
- Filter responses by role, AI usage frequency, experience, and focus area
- The full question text is shown above every chart
- Open-text responses are listed with a manual classification tool on the right side

## Classification system

Select an open-text question, create categories on the right panel, then click a response to select it and click a category to assign it. One response can belong to multiple categories. Click Save classifications to save your work - it reloads automatically the next time you start the app.


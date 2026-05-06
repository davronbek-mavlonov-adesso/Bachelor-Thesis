# Technical Documentation: AI Impact on IT Consulting Survey Dashboard


## 1. Overview

To support the analysis of the survey data collected as part of this thesis, a custom interactive dashboard was developed. The application runs locally on the user's machine and is accessed through a standard web browser. It does not require a server infrastructure, a database, or an active internet connection beyond the initial installation of its dependencies. The tool was designed to enable both quantitative exploration of closed survey questions and systematic manual classification of open-text responses.


## 2. Technology Stack

The application is built entirely in Python. The web framework used is Dash, an open-source framework developed by Plotly that enables the construction of reactive web applications using Python alone, without requiring JavaScript. Data visualization is handled by the Plotly library and survey data is processed using pandas. Application state that needs to persist between sessions is stored in a JSON file on disk.


## 3. Architecture

The application is organized into three layers: a data layer responsible for loading and transforming the raw data, an application layer that defines the user interface and handles all interaction logic, and a persistence layer that manages the saving and loading of classification data.

The data layer reads the survey CSV file on startup and transforms it from its original long format, where each row represents a single answer from a single respondent, into a wide format with one row per respondent and one column per question. Categorical columns such as AI usage frequency and years of experience are assigned a defined order so that charts display them correctly. The transformed data is held in memory for the duration of the session.

The application layer defines the visual structure of the dashboard and implements all reactive behavior. The layout is divided into a filter panel on the left, which allows narrowing results by role, usage frequency, experience, and focus area, and a main area on the right containing an interactive chart section and an open-text response section with a built-in classification tool. All user interaction, such as selecting a question, changing a filter, or assigning a response to a category, is handled through callback functions that update the relevant parts of the interface without reloading the page.

The persistence layer is responsible for reading and writing the classification data. When the user clicks the save button, the current classifications are written to a JSON file. The next time the application starts, this file is read automatically so that previous work is immediately available.


## 4. Classification System

The dashboard includes a manual classification tool for open-text questions. The user can define named categories for each question and assign individual responses to them. A single response can belong to multiple categories simultaneously. Categories are stored independently per question, meaning that categories created for one question do not appear under any other. Clicking a category filters the response list to show only the responses assigned to it, which makes it easier to review and refine groupings. All classifications are saved to disk manually using a dedicated save button.


## 5. Limitations

The application uses a development server and is intended for local use only. Classification data is saved manually, meaning that unsaved work is lost if the page is refreshed or the browser is closed before saving.

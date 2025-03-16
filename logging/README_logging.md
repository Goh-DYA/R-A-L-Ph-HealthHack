# RALPH Logs

This folder contains RALPH's logged documents.

There are 3 folders:
1. `/audiofiles`: Contains audio files of speech inputs and speech outputs (only applicable if there are speech inputs or speech outputs).
2. `/logs`: Chat system logs (in `.json` and `.log` format), including user inputs, intermediate outputs, knowledge base search results, runtime, etc.
3. `/summaries`: PDF files of conversation summaries (this is the PDF file that is emailed to the user).

There is also 1 helper notebook:
- `consolidate_logs.ipynb`: Consolidates all `.json` logs in the `/logs` folder into a readable CSV format.
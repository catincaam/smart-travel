# Deploy the dashboard

Use Streamlit Community Cloud at https://share.streamlit.io/.

1. Push the dashboard changes and deployment files to GitHub.
2. Sign in to Community Cloud and select **Create app**.
3. Choose repository `catincaam/smart-travel`, the branch containing these changes,
   and main file `dashboard/streamlit_app.py`.
4. In Advanced settings choose Python **3.12**.
5. Choose an available app subdomain and deploy.

Community Cloud uses `dashboard/requirements.txt` beside the entry point.
It contains only the dashboard's runtime dependencies, pinned to the versions
used locally. The root requirements file remains available for data collection,
notebooks, tests and the separate FastAPI service.

The dashboard uses the CSV files and images committed in this repository.
No API credentials are required for its current recommendation flow.
This deployment serves the dashboard only; it does not start the FastAPI API.

After deployment, check the recommendations, change a planner option, and open
the Interactive Map tab. Record the actual URL only after it is live.

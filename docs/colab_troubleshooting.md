# Colab website troubleshooting

Upload the ZIP through the Colab **Files sidebar**, then run the extraction, installation and **Build and download the results website** cells. Open the downloaded `EcoOrbit_Results_Website.html` as a local file in your browser. It contains all bundled data and graphics and does not use localhost or a proxy.

If Chrome blocks the automatic download, select the download permission prompt or find the file at `/content/EcoOrbit_v2/EcoOrbit_Results_Website.html` in Colab's Files sidebar, right-click, and choose **Download**. On macOS, open the downloaded HTML file from Finder; do not type `localhost` into the address bar.

If the website needs to reflect newly processed satellite output, rerun the build cell after the processing cell. If extraction fails, check `/content/EcoOrbit_813_Submission_Starter.zip`. If the browser is still blank, report the browser name and whether the HTML file has a size around 1.5 MB, along with any browser console error.

The optional notebook dashboard can show tables directly: `from src.colab_dashboard import show_section; show_section('Heat')`.

# Put EcoOrbit on GitHub and verify the submission

The ZIP extracts a folder named `EcoOrbit_v2`. Create a new **empty public repository** named `EcoOrbit` on GitHub (do not initialize it with a README or license). In Terminal on macOS/Linux, from the extracted folder:

```bash
cd /path/to/EcoOrbit_v2
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
jupyter nbconvert --to notebook --execute notebooks/02_main_analysis.ipynb --output /tmp/ecoorbit-executed.ipynb
python -m src.import_methane_plumes --published
python -m src.build_website
open EcoOrbit_Results_Website.html       # macOS; Linux: xdg-open EcoOrbit_Results_Website.html
```

On Windows PowerShell, use `py -3.11 -m venv .venv`, `.venv\Scripts\Activate.ps1`, then `start EcoOrbit_Results_Website.html`. If PowerShell blocks activation, run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and use that Python executable for subsequent `python` commands.

The notebook uses bundled **observed processed site features** and should complete in minutes without credentials or raw-scene downloads. It regenerates a model result and the website. The image outputs are already committed in `results/real/` and shown in the notebook and README. The Carbon Mapper examples are published source records, not site matches in Arizona, Algeria or Jeddah.

After checking the files, publish from inside `EcoOrbit_v2` (replace YOUR_USERNAME with your actual GitHub username):

```bash
git init -b main
git add README.md LICENSE requirements.txt .gitignore .github notebooks src data results docs dashboard.py EcoOrbit_Results_Website.html Run_EcoOrbit_Colab.ipynb make_sample.py
git status --short
git commit -m "EcoOrbit reproducible PoC"
git remote add origin https://github.com/YOUR_USERNAME/EcoOrbit.git
git push -u origin main
```

Authenticate through your Git credential manager or GitHub CLI. Never paste a token into code or commit it. `.gitignore` excludes raw imagery caches, generated model weights, private activity ledgers, and environment files. If you use `gh` after authentication, `gh repo create EcoOrbit --public --source=. --remote=origin --push` can replace the website creation, remote, and push steps.

Open the repository URL in a logged-out browser. Confirm the root README, pinned requirements, executed notebook with visible outputs, `data/sample_input/tanager_site_features_real.csv`, `results/real/classifier/all_city_test_metrics.png`, and the website HTML are visible. Open **Actions** and check that **Reproduce EcoOrbit PoC** passes. Paste that GitHub URL into the submission form, attach `docs/slides.pdf` to the form, and enter your actual registered team members and official theme in the README, form, and slide title. The source guide says the final submission deadline is **11 October 2026 at 23:59 in the team creator's local time**.

## Updating actual case plumes

1. Export CH4/CO2 plume records as CSV or GeoJSON from [Carbon Mapper](https://data.carbonmapper.org/). Their platform may require a scoped account token for API endpoints; keep it out of the repository. Ensure your export has latitude, longitude, gas, plume ID, date, quality and the original emission/uncertainty fields.
2. Run `python -m src.import_methane_plumes /path/to/export.csv`.
3. Inspect `results/real/methane/plume_matches.csv` for candidate records within 20 km of the registered targets. Zero rows means no matches in that export, not zero emissions.
4. Run `python -m src.build_website` and reopen the HTML. Review every candidate's original image, location, wind and quality before making any attribution claim.

The three source-linked published examples work immediately with `python -m src.import_methane_plumes --published`; they populate `results/real/methane/published_plume_results.csv` and the website without login. The provider's image links require internet when you open them. See `docs/DATA_ATTRIBUTION.md` for redistribution terms.

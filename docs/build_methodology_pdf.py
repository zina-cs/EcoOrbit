"""Build the judge-facing method report from actual observed results."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.graphics.shapes import Drawing,Rect,String,Line
ROOT=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Eco',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9));styles['Title'].textColor=colors.HexColor('#145951')
def p(s):return Paragraph(s,styles['Eco'])
def h(s):return Paragraph(s,styles['Heading2'])
def tab(rows,widths):
 t=Table([[p(str(v)) for v in r] for r in rows],colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1f0e9')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#becfc8')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]));return t

def diagram():
 d=Drawing(480,160)
 labels=[['NASA EMIT + ERA5','Pixel selection + mass','Diagnostic gas evidence'],['Tanager + Sentinel-2','Spectral / spatial features','ML + multispectral context']]
 for row,items in enumerate(labels):
  y=105-row*75
  for col,label in enumerate(items):
   x=col*165;d.add(Rect(x,y,150,44,fillColor=colors.HexColor('#e1f0e9'),strokeColor=colors.HexColor('#145951'),radius=6));d.add(String(x+75,y+22,label,fontName='Helvetica',fontSize=8,textAnchor='middle'))
   if col<2:d.add(Line(x+150,y+22,x+165,y+22,strokeColor=colors.HexColor('#145951')))
 return d

def build():
 summaries=json.loads((ROOT/'results/real/emit_pixels/case_summaries.json').read_text())
 story=[Paragraph('EcoOrbit',styles['Title']),p('<b>Methane and carbon intelligence</b><br/>Challenge: Air Intelligence | Team: EcoOrbit'),h('Solution and evidence boundary'),p('A reproducible proof of concept for reviewing real methane plume pixels, wind, selected excess mass and diagnostic flux. Published CO2 observations provide separate reference evidence; EcoOrbit has not retrieved landfill CO2 pixels. NO2/SO2 and multispectral site context support follow-up.'),diagram(),h('Real observed cases')]
 rows=[['Event','Peak ppm m','Wind m/s','Selected excess CH4 kg']]
 for s in summaries:rows.append([s['case_id'].replace('_',' '),round(s['max_raw_enhancement_ppmm']),round(s['wind_m_s'],2),round(s['scenarios'][0]['integrated_excess_ch4_kg'])])
 story+=[tab(rows,[180,80,75,145]),Spacer(1,10),p('Mass is a selected snapshot quantity, not an emission rate. Jeddah uses source-scene sensitivity and uncertainty; Brazil uses original plume rasters without inventing companion corrections. Flux scenarios are unvalidated and excluded from annual inventories.'),PageBreak(),h('Preprocessing implemented in code'),tab([
 ['Stage','Provider input / EcoOrbit operation','Code'],
 ['Acquire','Real EMIT TIFF/GeoJSON and ERA5; Tanager source scene IDs and site registry.','emit_cases.py; multisite_download.py'],
 ['Calibration / atmosphere','Provider gas retrieval and L2 surface products. EcoOrbit does not rerun radiance calibration or atmospheric correction. Landsat values are scaled to Celsius.','site_heat.py; train_classifier.py'],
 ['Geometry / QA','Coordinate transforms, local sampling, cloud/cirrus/no-data rejection; actual WGS84 plume pixel areas.','train_classifier.py; emit_pixels.py'],
 ['Spectral binning','11 x 11 Tanager site windows, >=50 valid pixels; 30 nm bins excluding strong water absorption; spatial medians and indices.','train_classifier.py'],
 ['Methane preparation','Jeddah: ENH/SENS, background subtraction, sensitivity 0.5-2 and SNR>=2. Brazil: vetted PLM mask and enhancement thresholds only.','emit_pixels.py; emit_cases.py'],
 ['Multispectral preparation','Sentinel-2 B04/B08/B11 + SCL; 20 m grid, site/reference NDVI/NDBI. Landsat QA and site/reference surface temperature.','site_land.py; site_heat.py']],[90,275,115]),PageBreak(),h('Analysis and machine learning'),p('<b>Gas analysis:</b> convert ppm m to column mass using the ideal gas law and pixel area; sum selected excess methane. Review thresholds of 500, 1000 and 1500 ppm m. ERA5 supplies real hourly overpass context. Diagnostic Q = 3600 x wind x integrated mass / maximum selected-pixel separation.'),p('This is processing of NASA spectral retrievals, not a new matched-filter retrieval from radiance. Whole-complex geometry, coarse wind, unverified source origin and incomplete uncertainty prevent a validated facility rate.'),p('<b>Supplementary ML:</b> median imputation, standardization, PCA and balanced logistic regression. A fixed city/label-stratified split uses 36 training and 12 test sites across all three cities. Three-fold training-only validation chooses 4/8/12 components. Observed accuracy is 11/12 (91.7%), AUC 0.944.'),p('Labels distinguish industrial registry sites from school controls. This small screen does not establish universal factory/landfill accuracy and does not estimate methane. Green image patches provide separate vegetation context.'),h('Multispectral example'),p('Sentinel-2 L2A provides two-date vegetation and built-surface indices; Landsat C2 L2 provides surface-temperature contrasts. Completed US observations are separate in location and date from the landfill events. They demonstrate additional site investigation, not plume attribution.'),h('Carbon and reporting'),p('A source-reported CO2 reference at an Indian power-generation site demonstrates published hyperspectral carbon evidence. It is not a new EcoOrbit retrieval. GRI 305 and GHG Protocol evidence mapping distinguishes satellite observations from activity-based annual inventories; no annual Scope 1/2 CO2e is inferred.'),PageBreak(),h('Judge walkthrough and reproduction'),p('<b>Solution:</b> select one of three real methane observations, inspect pixels and wind, compare mask thresholds and diagnostic flux, and inspect separate published CH4/CO2 references.<br/><b>Methodology:</b> review provider preprocessing, actual code operations, ML evaluation and reporting boundaries.<br/><b>Additional features:</b> inspect US site maps, Tanager material/site classification, Sentinel-2 changes, Landsat heat and relevant NO2/SO2.'),p('From the project root:<br/><font face="Courier">python -m pip install -r requirements.txt<br/>python -m src.emit_cases<br/>python -m src.evaluate_sites<br/>python -m src.build_website</font>'),p('Use notebooks/02_main_analysis.ipynb and notebooks/04_emit_pixel_analysis.ipynb. Real processed inputs and small source crops are bundled; full raw imagery has documented download commands. Colab downloads a standalone HTML website without a localhost proxy.'),h('Primary methods and provenance'),p('NASA EMIT trace-gas ATBD and user guide:<br/>https://github.com/emit-sds/emit-sds-tgp/tree/develop/docs<br/>ERA5 via Open-Meteo historical archive:<br/>https://open-meteo.com/en/docs/historical-weather-api<br/>Exact inputs, hashes and processing limitations: results/real/emit_pixels/case_summaries.json and docs/EMIT_PIXEL_METHOD.md.'),p('Detailed gas thresholds and source-scene IDs are retained in the input/output manifests. Only real observations are used in this release.')]
 def footer(c,d):c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#145951'));c.drawString(42,26,'EcoOrbit | Air Intelligence | Observed-data PoC');c.drawRightString(550,26,str(d.page))
 SimpleDocTemplate(str(ROOT/'docs/methodology_report.pdf'),pagesize=(595,842),leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
if __name__=='__main__':build()

"""Generate the compact methodology and evidence report from observed outputs."""
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, String, Line

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/methodology_report.pdf'
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleEco',parent=styles['Title'],fontName='Helvetica-Bold',
                          fontSize=23,leading=27,textColor=colors.HexColor('#0C3635'),spaceAfter=14))
styles.add(ParagraphStyle(name='HEco',parent=styles['Heading2'],fontName='Helvetica-Bold',
                          fontSize=13,leading=16,textColor=colors.HexColor('#0C5552'),spaceBefore=15,spaceAfter=7))
styles.add(ParagraphStyle(name='BodyEco',parent=styles['BodyText'],fontName='Helvetica',
                          fontSize=9.3,leading=13,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallEco',parent=styles['BodyText'],fontName='Helvetica',
                          fontSize=8,leading=10,spaceAfter=5))


def para(s, style='BodyEco'):
    return Paragraph(s, styles[style])


def table(rows, widths):
    t=Table([[para(str(c),'SmallEco') for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDECEA')),
        ('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#B8CBC8')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    return t


def diagram():
    d=Drawing(500,245)
    columns=[(0,'CH4 case registry','TROPOMI QA; near/background','Regional XCH4 evidence'),
             (170,'Carbon Mapper export','Plume QA, wind, source review','Plume candidate evidence'),
             (340,'Tanager + land use','30 nm bins; site classifier','Supporting site context')]
    for x,a,b,c in columns:
        for y,label in [(190,a),(110,b),(30,c)]:
            d.add(Rect(x,y,155,44,rx=5,ry=5,fillColor=colors.HexColor('#EAF4F2'),
                       strokeColor=colors.HexColor('#23716D'),strokeWidth=1))
            d.add(String(x+77.5,y+18,label,textAnchor='middle',fontName='Helvetica-Bold',fontSize=8.3,
                         fillColor=colors.HexColor('#123F3C')))
        for y in [155,75]:
            d.add(Line(x+77.5,y+35,x+77.5,y,strokeColor=colors.HexColor('#23716D'),strokeWidth=1.5))
            d.add(Line(x+72.5,y+5,x+77.5,y,strokeColor=colors.HexColor('#23716D')))
            d.add(Line(x+82.5,y+5,x+77.5,y,strokeColor=colors.HexColor('#23716D')))
    return d


def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526B68'))
    canvas.drawString(40,28,'EcoOrbit | observed US research pilot | 29 Sep 2026')
    canvas.drawRightString(555,28,f'Page {doc.page}')
    canvas.restoreState()


def build():
    doc=SimpleDocTemplate(str(OUT),pagesize=(595,842),rightMargin=42,leftMargin=42,
                          topMargin=40,bottomMargin=48)
    story=[para('EcoOrbit: methane and pollutant intelligence','TitleEco'),
      para('CH4 case studies, quality-screened atmospheric columns and supporting land-use classification'),
      para('<b>Scope.</b> Methane case targets: Stanford Arizona controlled-release location (2022 verified study), Hassi R Mel Algeria approximate field center, and Jeddah Wadi Al-Asla landfill. New case-specific CH4 scenes are pending. The 24 observed US industrial points and 24 school controls support an additional land-use classifier.'),
      para('Methane case evidence','HEco'),
      table([['Case','Coordinate','Evidence status'],['Stanford Arizona','32.82182, -111.78577','2022 published releases; suggested 2024-25 period unverified'],['Hassi R Mel','about 32.9, 3.2','Published regional methane study; not a surveyed stack'],['Jeddah landfill','21.64419, 39.39026','Landfill location documented; three proposed 2024 dates unverified']],[130,130,251]),
      para('TROPOMI CH4 workflow: XCH4 ppb, QA > 0.5; compare 0-25 km to 25-80 km ring, requiring three valid pixels each. A contrast is regional evidence, never source attribution or an emission rate. Optional Carbon Mapper CH4 and CO2 plume exports add quality, wind, instantaneous gas-specific kg/h and uncertainty. No target CO2 plume is bundled.'),
      para('Real published plume examples','HEco'),
      table([['Location / gas','Date','Provider-reported rate'],['Brazil landfill / CH4','29 Sep 2024','Preliminary plume: 2,836 kg/h'],['India power generation / CO2','1 Nov 2024','Preliminary source: 838,000 kg/h'],['EMIT example / CH4','20 Apr 2024','3,610.58 +/- 377.95 kg/h']],[180,85,246]),
      para('These are source-linked published examples, not emissions at the three proposed case sites. The first two image IDs are given in provider image filenames; the original article omits exact origin coordinates and uncertainty. See data/published_plumes.csv.'),
      para('Pipeline','HEco'),diagram(),
      para('Preprocessing and calibration','HEco'),
      table([['Input','Applied processing','Interpretation'],
        ['Planet Tanager L2A','Provider radiometric, atmospheric and geometric corrections; HDF no-data/cloud/cirrus masks; 30 nm reflectance bins and three spectral indices.','Site spectral features, not a raw sensor calibration.'],
        ['Landsat 8/9 L2','QA_PIXEL mask; Celsius = DN x 0.00341802 + 149 - 273.15. 180 m site median minus 600-1200 m annulus.','Land surface contrast; thermal information coarser than 30 m output grid.'],
        ['Sentinel-2 L2A','SCL clear pixels; two-date NDVI=(B08-B04)/(B08+B04); NDBI=(B11-B08)/(B11+B08).','Land change can reflect season and cover.'],
        ['Sentinel-5P L2','NO2 QA >0.75; SO2 QA >0.5; nearest valid pixel center within 15 km.','Atmospheric column mol/m2, not stack emission or ground concentration.']],
        [105,235,171]),
      PageBreak(),para('Supporting land use and observed coverage','TitleEco'),
      para('The 60 site features (57 reflectance bins plus NDVI, NDBI and MNDWI) are processed by imputation, scaling, eight-component PCA and balanced logistic regression. A fixed stratified split trains on 36 sites and tests on 12, two per class in each city. Model selection uses training-only cross-validation; schools are narrow comparison controls.'),
      table([['Evaluation','Sites','Accuracy','ROC AUC'],['All-city test','12','0.917','0.944'],['Train-only CV','36','0.722','-'],['Earlier city holdout','48','0.750','0.804']],[200,80,110,121]),
      Spacer(1,9),para('Primary test confusion matrix (true school/industrial by predicted school/industrial): [[5,1],[0,6]]. The 424 additional registry points have no extracted spectra and are excluded from training. Schools are a narrow built-environment negative class. A new script retrieves OSM green-space and commercial polygon candidates; expanded test metrics are pending source imagery QA.','SmallEco'),
      para('Coverage of added observations','HEco'),
      table([['Result','Detroit','Jacksonville','Rochester'],
             ['Landsat valid sites / site-date rows','3 / 6','8 / 16','8 / 16'],
             ['Two-date Sentinel-2 paired sites','2','6','0'],
             ['NO2 and SO2 in supplied file','8 sites each','Download pending','No image-week items']],
            [225,95,95,96]),
      Spacer(1,8),para('The available Landsat median site-minus-nearby-land contrasts are +0.66 C (Detroit), +1.45 C (Jacksonville) and +4.00 C (Rochester), on different dates and backgrounds. They must not be ranked as factory heat-emission rates.'),
      para('Jacksonville Tanager green reference: 12 separated, clear vegetation-rich image patches. Cluster-wide median NDVI 0.770 versus median 0.305 across eight industrial-site neighborhoods (difference +0.465). The cluster median is not 12 independent patch measurements; no verified park geometry or emission inference is claimed.'),
      para('Limits and ESG reporting status','HEco'),
      para('A TROPOMI cell spans kilometres and can include multiple factories and other sources. The nearest pixel center is a geographic lookup only. Negative SO2 retrievals near background are measurement noise, not negative physical emissions. ERA5 10 m wind and CAMS modeled air provide regional context, not a factory plume or discharge rate.'),
      para('GRI 305-1/305-2 and the GHG Protocol require organizational boundaries, fuel/process and electricity records, factors and uncertainty for Scope 1/2 tCO2e. GRI 305-7 requires measured or justified NOx/SOx mass estimates. Satellite columns and wind provide context, not these quantities. The generated report is an evidence-gap demonstration, not a conforming disclosure.'),
      para('Carbon accounting and interactive results','HEco'),
      para('A documented facility activity CSV drives Scope 1 and Scope 2 tonnes CO2e per declared period; the dashboard shows unavailable when records are missing. Carbon Mapper CO2 or CH4 plume kg/h is instantaneous and cannot be annualized without persistence and a reporting boundary. Interactive tabs filter gas, case, date, NO2, SO2, particulate model context and aerosol products.'),
      para('Reproducibility','HEco'),
      para('Open the included dashboard with: streamlit run dashboard.py. The notebook and scripts reproduce the workflow. Source snapshots, exact scene IDs, QA thresholds, dates and missing statuses accompany the CSV outputs. See README.md and docs/methodology.md for the complete sources and correction steps.'),
      para('Sources: Planet Tanager docs; USGS Landsat Collection 2 Surface Temperature; EPA FRS API; Copernicus Sentinel-5P NO2 and SO2 product readmes; Microsoft Planetary Computer; Open-Meteo CAMS and ERA5 access. Full URLs are in docs/methodology.md.','SmallEco')]
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)

if __name__=='__main__':build()

"""Run from the EcoOrbit folder: streamlit run dashboard.py"""
from pathlib import Path
import os,json,pandas as pd,streamlit as st
ROOT=Path(__file__).parent;RES=ROOT/'results/real'
st.set_page_config(page_title='EcoOrbit | Methane and air intelligence',layout='wide')
def read(path):
 if not path.exists():return pd.DataFrame()
 try:
  data=pd.read_csv(path)
  if 'facility_id' in data:data['facility_id']=data['facility_id'].astype(str)
  return data
 except pd.errors.EmptyDataError:return pd.DataFrame()
CHAT_STARTERS=[
 'What did EcoOrbit measure at Jeddah on 9 June 2024?',
 'What does the 11/12 classifier result actually mean?',
 'Can we attribute the methane plume to the landfill?',
 'What is diagnostic flux versus an annual inventory?',
 'Why is there no landfill CO2 retrieval?',
]
CHAT_SYSTEM='''You are EcoOrbit Chat, the explainable-AI assistant for the EcoOrbit Arab Youth Hackathon proof of concept (Air Intelligence).
Scope: answer only questions about this project, its satellite data, processing, results, limits, sites, gases (CH4, CO2, NO2, SO2), wind, heat, land indices, the industrial-versus-school classifier, ESG/GRI 305 / GHG Protocol evidence gaps, how to run the dashboard, and closely related Earth-observation interpretation.
If a question is off-topic (general trivia, unrelated coding, news, homework, other products, or anything not grounded in EcoOrbit), refuse in the user's language. Do not answer it. Briefly say you only discuss EcoOrbit evidence, then offer 2-3 on-topic example questions.
Language: reply in the same language the user wrote (English or Arabic). Keep scientific terms (EMIT, CH4, ppm·m, GRI 305) in their standard form.
XAI rules:
- Ground every quantitative claim in the PROJECT BRIEFING below. Name the result file or method when you use a number.
- If the briefing does not contain a value, say it is not in the packaged evidence. Never invent coordinates, rates, accuracies, or dates.
- Explain why a result looks the way it does (processing choices, thresholds, QA, spatial scale).
- Repeat the project's honest limits: nearby catalog footprints do not prove the landfill emitted the gas; diagnostic Simple-IME flux is not a validated facility rate; snapshots cannot be annualized; CO2 at the landfills is not a new EcoOrbit retrieval; NO2/SO2 are coarse columns not stack emissions; the 11/12 score is a small industrial-versus-school screen.
Team: EcoOrbit. Challenge: Air Intelligence. Primary gas workflow: NASA EMIT methane pixels for Jeddah (9 June 2024) and Seropédica (5 March and 24 September 2024).'''
def _env_gemini_key():
 for name in ('GEMINI_API_KEY','GOOGLE_API_KEY','GOOGLE_GENAI_API_KEY'):
  v=os.environ.get(name,'').strip()
  if v: return v
 env_path=ROOT/'.env'
 if env_path.exists():
  for line in env_path.read_text(encoding='utf-8').splitlines():
   line=line.strip()
   if not line or line.startswith('#') or '=' not in line: continue
   key,val=line.split('=',1)
   if key.strip() in ('GEMINI_API_KEY','GOOGLE_API_KEY','GOOGLE_GENAI_API_KEY'):
    val=val.strip().strip('"').strip("'")
    if val: return val
 return ''
def _text_clip(path,n=8000):
 p=ROOT/path
 return p.read_text(encoding='utf-8')[:n] if p.exists() else ''
@st.cache_data(show_spinner=False)
def _chat_briefing():
 parts=['EcoOrbit bundled evidence. Do not contradict these files.']
 cases=ROOT/'results/real/emit_pixels/case_summaries.json'
 if cases.exists():
  rows=json.loads(cases.read_text(encoding='utf-8'))
  slim=[{k:row[k] for k in row if k!='input_manifest'} for row in rows]
  parts.append('EMIT pixel case summaries (results/real/emit_pixels/case_summaries.json):\n'+json.dumps(slim,ensure_ascii=False,default=str)[:20000])
 emit=read(RES/'landfill_gases/emit_search.csv')
 if not emit.empty:
  keep=[c for c in ('site_id','gas','granule_id','plume_distance_km','status') if c in emit.columns]
  parts.append('NASA EMIT catalog footprints (results/real/landfill_gases/emit_search.csv):\n'+emit[keep].to_csv(index=False))
 for rel,label in [
  ('data/published_plumes.csv','Published plume examples'),
  ('results/real/methane/case_status.csv','Methane case status'),
  ('results/real/methane/observed_us_regional_ch4.csv','US regional TROPOMI CH4'),
  ('results/real/classifier/all_city_test_metrics.json','Held-out classifier metrics'),
  ('results/real/classifier/all_city_test_predictions.csv','Held-out classifier predictions'),
  ('results/real/carbon/status.json','Carbon inventory status'),
  ('results/real/green_reference_summary.json','Green reference summary'),
 ]:
  p=ROOT/rel
  if not p.exists(): continue
  if p.suffix=='.json': parts.append(f'{label} ({rel}):\n'+p.read_text(encoding='utf-8')[:6000])
  else: parts.append(f'{label} ({rel}):\n'+read(p).head(40).to_csv(index=False))
 poll=read(RES/'pollutants/site_no2_so2.csv')
 if not poll.empty:
  parts.append('NO2/SO2 coverage counts:\n'+poll.groupby(['city','product','status']).size().to_string())
  cols=[c for c in ('city','name','date','product','column_mol_m2','nearest_pixel_center_km','status') if c in poll.columns]
  parts.append('NO2/SO2 sample rows (results/real/pollutants/site_no2_so2.csv):\n'+poll[cols].head(24).to_csv(index=False))
 heat=read(RES/'heat/site_heat.csv')
 if not heat.empty: parts.append('Landsat heat (results/real/heat/site_heat.csv):\n'+heat.head(30).to_csv(index=False))
 land=read(RES/'land/site_change.csv')
 if not land.empty: parts.append('Sentinel-2 land change (results/real/land/site_change.csv):\n'+land.head(20).to_csv(index=False))
 for rel in ('docs/EMIT_PIXEL_METHOD.md','docs/methodology.md','README.md','results/real/esg_gri305_evidence.md'):
  clip=_text_clip(rel,9000)
  if clip: parts.append(f'{rel}:\n'+clip)
 return '\n\n'.join(parts)
def _gemini_answer(api_key,question,history):
 from google import genai
 from google.genai import types
 client=genai.Client(api_key=api_key)
 contents=[]
 for turn in history:
  role='user' if turn['role']=='user' else 'model'
  contents.append(types.Content(role=role,parts=[types.Part(text=turn['content'])]))
 contents.append(types.Content(role='user',parts=[types.Part(text=question)]))
 models=[]
 remembered=st.session_state.get('eo_gemini_model')
 if remembered: models.append(remembered)
 for name in ('gemini-2.5-flash','gemini-2.0-flash','gemini-flash-latest','gemini-3.8-flash'):
  if name not in models: models.append(name)
 errors=[]
 instruction=CHAT_SYSTEM+'\n\nPROJECT BRIEFING:\n'+_chat_briefing()
 for model in models:
  try:
   resp=client.models.generate_content(model=model,contents=contents,config=types.GenerateContentConfig(system_instruction=instruction,temperature=0.2))
   text=(resp.text or '').strip()
   if not text: raise RuntimeError('empty model response')
   st.session_state.eo_gemini_model=model
   return text
  except Exception as err:
   errors.append(f'{model}: {err}')
 raise RuntimeError('Gemini request failed. '+'; '.join(errors)[:700])
sites=read(ROOT/'data/training_sites.csv');factories=sites[sites.label.eq(1)] if not sites.empty else pd.DataFrame()
pred=read(RES/'classifier/factory_screening_results.csv')
metric=read(RES/'classifier/all_city_test_predictions.csv')
candidates=read(ROOT/'data/candidate_factories.csv')
control_candidates=read(ROOT/'data/candidate_controls.csv')
air=read(RES/'air_by_city.csv');wind=read(RES/'wind_by_city.csv')
aot=read(RES/'aot/multicity_aot_comparison.csv')
heat=read(RES/'heat/site_heat.csv');land=read(RES/'land/site_change.csv');pollutants=read(RES/'pollutants/site_no2_so2.csv')
st.title('EcoOrbit | Methane and pollutant intelligence')
st.caption('Methane and other atmospheric pollutants are the primary study. The US industrial-site hyperspectral classifier is an additional land-use screen. Regional columns do not establish source emissions.')
if factories.empty:st.error('Run the data workflow to create data/training_sites.csv.');st.stop()
city=st.sidebar.selectbox('Metro area',['All cities']+sorted(factories.city.unique().tolist()))
view=factories if city=='All cities' else factories[factories.city.eq(city)]
shown=view.merge(pred[['facility_id','factory_screen_score']] if not pred.empty else pd.DataFrame(columns=['facility_id','factory_screen_score']),on='facility_id',how='left')
selected=st.sidebar.selectbox('Factory',shown.facility_id,format_func=lambda k:shown.loc[shown.facility_id.eq(k),'name'].iloc[0])
site=shown.set_index('facility_id').loc[selected]
methane_tab,air_tab,map_tab,class_tab,heat_tab,esg_tab,chat_tab=st.tabs(['CH₄ and CO₂','NO₂, SO₂ and aerosols','Land-use sites','Hyperspectral classification','Surface context','Carbon and ESG results','EcoOrbit Chat'])
with methane_tab:
 st.subheader('Published, real hyperspectral plumes')
 published=read(ROOT/'data/published_plumes.csv')
 if not published.empty:
  selected_gas=st.radio('Real plume gas', ['CH4','CO2'],horizontal=True,key='published_gas')
  known=published[published.gas.eq(selected_gas)]
  plume_id=st.selectbox('Observed plume',known.plume_id.tolist(),format_func=lambda key:known.set_index('plume_id').loc[key,'site_name'],key='published_plume')
  chosen=known[known.plume_id.eq(plume_id)].iloc[0]
  st.metric('Reported rate',f"{chosen.reported_rate_kg_h:,.0f} kg {selected_gas}/h")
  st.caption(f"{chosen.rate_basis}; published {chosen.scene_timestamp}. This is a reported observation, not an annual inventory. Missing uncertainty remains unknown.")
  st.dataframe(known[['site_name','site_type','scene_timestamp','reported_rate_kg_h','rate_basis','emission_uncertainty_kg_h','wind_speed_m_s','source_url']],hide_index=True,width='stretch')
  mapped=known.dropna(subset=['latitude','longitude'])
  if not mapped.empty:st.map(mapped[['latitude','longitude']],size=120)
  st.markdown(f'[Open primary source and plume context]({chosen.source_url})')
  if pd.notna(chosen.image_url) and str(chosen.image_url).startswith('https://'):
   try:st.image(chosen.image_url,caption=f'{chosen.site_name}: published {selected_gas} plume',width='stretch')
   except Exception:st.info('Image preview unavailable; open the source image link below.')
   st.markdown(f'[Open published plume image]({chosen.image_url})')
  st.caption('The Brazil landfill and India power-generation observations are different sites from the three proposed targets. Their article supplies the rate and image but not exact origin coordinates or uncertainty. The Yemen example supplies exact plume metadata in the Carbon Mapper product guide.')
 st.subheader('CH₄ and CO₂ case-study evidence')
 registered=read(ROOT/'data/methane_sites.csv');statuses=read(RES/'methane/case_status.csv')
 selected_methane_site=st.selectbox('Methane / carbon case', ['All cases']+registered.site_id.tolist(),format_func=lambda key:key if key=='All cases' else registered.set_index('site_id').loc[key,'name'],key='methane_site') if not registered.empty else 'All cases'
 if not registered.empty:
  st.map(registered[['latitude','longitude']],latitude='latitude',longitude='longitude',size=100)
  st.dataframe(registered[['name','country','site_type','latitude','longitude','analysis_start','analysis_end','verification','source_url']],hide_index=True,width='stretch')
 st.caption('Stanford controlled releases are documented at this location in 2022; the proposed 2024–25 period is not verified. Hassi R Mel is an approximate gas-field point. The three Jeddah dates are user-proposed windows, not established detections.')
 if not statuses.empty:st.dataframe(statuses if selected_methane_site=='All cases' else statuses[statuses.site_id.eq(selected_methane_site)],hide_index=True,width='stretch')
 case=read(RES/'methane/regional_ch4.csv')
 if not case.empty:
  st.subheader('QA-screened TROPOMI XCH₄ (regional)')
  if selected_methane_site!='All cases':case=case[case.site_id.eq(selected_methane_site)]
  if 'date' in case and case.date.notna().any():
   dates=sorted(case.date.dropna().astype(str).unique().tolist())
   selected_dates=st.multiselect('Observation dates',dates,default=dates,key='methane_dates')
   case=case[case.date.astype(str).isin(selected_dates)]
  st.dataframe(case,hide_index=True,width='stretch')
  st.caption('Near: 0–25 km. Background: 25–80 km. Difference in ppb is a regional column contrast, not a facility plume or emission rate. Empty or failed downloads are not zero emissions.')
 else:st.info('Case-specific satellite scenes are not bundled. Run python -m src.methane_cases after installation to download and analyze actual L2 observations.')
 plume=read(RES/'methane/plume_matches.csv')
 if not plume.empty:
  st.subheader('Hyperspectral CH₄ and CO₂ plume candidates')
  gases=sorted(plume.gas.dropna().unique().tolist()) if 'gas' in plume else ['CH4']
  chosen_gas=st.selectbox('Plume gas',gases,key='plume_gas')
  visible=plume[plume.gas.eq(chosen_gas)] if 'gas' in plume else plume
  selected_case=st.selectbox('Case site', ['All sites']+sorted(visible.site_id.dropna().unique().tolist()),key='plume_case',index=(['All sites']+sorted(visible.site_id.dropna().unique().tolist())).index(selected_methane_site) if selected_methane_site in visible.site_id.dropna().tolist() else 0)
  if selected_case!='All sites':visible=visible[visible.site_id.eq(selected_case)]
  st.dataframe(visible,hide_index=True,width='stretch')
  if {'plume_latitude','plume_longitude'}.issubset(visible.columns) and not visible.empty:
   st.map(visible.rename(columns={'plume_latitude':'latitude','plume_longitude':'longitude'})[['latitude','longitude']],size=75)
  if 'instantaneous_emission_kg_h' in visible and visible.instantaneous_emission_kg_h.notna().any():
   st.bar_chart(visible.set_index('plume_id')['instantaneous_emission_kg_h'])
  st.caption('kg/h is an instantaneous gas-specific plume estimate, not annual CO₂e or an attribution solely from proximity. Review original imagery, quality, wind and uncertainty.')
 else:st.info('For site-level CH₄ or CO₂ plumes, export Carbon Mapper records and run python -m src.import_methane_plumes FILE.csv.')
 st.subheader('Existing measured US regional CH₄ context')
 chart=RES/'methane/observed_us_regional_ch4.png'
 if chart.exists():st.image(str(chart),width='stretch')
 for name in ['Jacksonville','Detroit','Rochester']:
  sample=read(RES/f'atmosphere/{name.lower()}_ch4.csv')
  if not sample.empty:st.write(name);st.dataframe(sample[['date','n_valid','median','p95','status']],hide_index=True,width='stretch')
with map_tab:
 st.subheader('Sourced US facilities')
 st.map(view[['latitude','longitude']],latitude='latitude',longitude='longitude',size=35)
 st.dataframe(shown[['city','name','latitude','longitude','valid_fraction_150m','factory_screen_score','source_url']],hide_index=True,width='stretch')
 if not candidates.empty:
  st.write(f'Additional EPA registry candidates awaiting hyperspectral QA and label checks: {len(candidates)}')
  st.dataframe(candidates[candidates.city.eq(city)] if city!='All cities' else candidates,hide_index=True,width='stretch')
 st.caption('EPA Facility Registry Service TRI points. A registry location is not a surveyed building footprint; current operating status is not independently checked.')
with class_tab:
 st.subheader('Hyperspectral industrial-site screen')
 st.metric('Exploratory score at selected factory',f'{site.factory_screen_score:.2f}' if pd.notna(site.factory_screen_score) else 'Unavailable')
 st.caption('Current scores use 24 listed industrial sites and 24 schools. Schools are a narrow built-environment comparison. Green and commercial candidates require QA before scoring.')
 if not control_candidates.empty:
  st.write('OSM green-space and commercial candidates (unverified)')
  st.dataframe(control_candidates[control_candidates.city.eq(city)] if city!='All cities' else control_candidates,hide_index=True,width='stretch')
 else:st.info('Run python -m src.add_control_sites --fetch to acquire real green-space and commercial polygon candidates.')
 expanded=RES/'classifier/expanded/all_city_test_metrics.json'
 if expanded.exists():
  import json
  em=json.loads(expanded.read_text());st.write('Expanded-control independent test:',em)
 summary=RES/'classifier/all_city_test_metrics.json'
 if summary.exists():
  import json
  m=json.loads(summary.read_text())
  st.metric('All-city site test accuracy',f"{m['test_accuracy']:.1%}",help='11 of 12 held-out sites; two per class per city. Small and narrow comparison sample.')
  st.write('Test ROC AUC:',round(m['test_auc'],3))
 if not metric.empty:st.dataframe(metric,hide_index=True,width='stretch')
 fig=RES/'classifier/all_city_test_metrics.png'
 if fig.exists():st.image(str(fig),caption='36 training sites; 12 held-out sites across all three cities.',width='stretch')
 if city in ('All cities','Jacksonville'):
  fig=RES/'hyperspectral_classification.png'
  if fig.exists():st.image(str(fig),caption='Jacksonville hyperspectral material clusters and two example factory points.',width='stretch')
 st.subheader('Observed green reference: Jacksonville Tanager')
 green_summary=RES/'green_reference_summary.json'
 if green_summary.exists():
  import json
  gs=json.loads(green_summary.read_text())
  st.write(f"Twelve separated vegetation-rich image patches; green-cluster NDVI median {gs['green_cluster_ndvi_median']:.3f} versus {gs['factory_site_count']} factory-neighborhood NDVI median {gs['factory_site_ndvi_median']:.3f} (difference {gs['ndvi_reference_minus_factory']:+.3f}).")
  st.caption('The green value is a cluster-wide pixel median, not twelve independent patch measurements. Patches have image row/column locations, not verified park parcels; different spatial supports prevent treating this as a matched emissions or classifier test.')
  col1,col2=st.columns(2)
  with col1:st.image(str(RES/'green_reference_map.png'),width='stretch')
  with col2:st.image(str(RES/'green_reference_comparison.png'),width='stretch')
  st.dataframe(read(RES/'green_reference_patches.csv'),hide_index=True,width='stretch')
 st.caption('Material clustering and the site classifier answer different questions. Verified factory polygons and broader nonfactory examples are needed for operational classification.')
with heat_tab:
 st.subheader('Landsat land surface temperature')
 st.caption('Site 180 m circle versus surrounding 600–1200 m annulus. This is surface temperature, not stack heat; thermal information is coarser than the 30 m output grid.')
 if not heat.empty:
  subset=heat if city=='All cities' else heat[heat.city.eq(city)]
  chosen=subset[subset.facility_id.eq(str(selected))]
  if not chosen.empty:
   st.metric('Selected factory: median surface contrast',f'{chosen.surface_excess_c.median():+.2f} °C')
  else:st.info('No QA-valid Landsat comparison for the selected factory in the supplied scenes.')
  st.dataframe(subset[['city','name','date','surface_c','reference_c','surface_excess_c','near_pixels','scene_id']],hide_index=True,width='stretch')
  if not subset.empty:st.bar_chart(subset.groupby('city').surface_excess_c.median())
 else:st.info('Run python -m src.site_heat.')
 st.subheader('Sentinel-2 NDVI and NDBI change')
 if not land.empty:
  subset=land if city=='All cities' else land[land.city.eq(city)]
  chosen=subset[subset.facility_id.eq(str(selected))]
  if not chosen.empty and chosen.ndvi_site_change.notna().any():
   st.metric('Selected factory: NDVI change',f'{chosen.ndvi_site_change.iloc[0]:+.3f}')
  else:st.info('No paired clear Sentinel-2 observations for the selected factory.')
  cols=[c for c in ['city','name','ndvi_site_earlier','ndvi_site_later','ndvi_site_change','ndbi_site_change'] if c in subset]
  st.dataframe(subset[cols],hide_index=True,width='stretch')
 else:st.info('Run python -m src.site_land.')
with air_tab:
 st.subheader('Interactive pollutant results')
 pollutant=st.selectbox('Select pollutant', ['NO₂','SO₂','UV aerosol index','Sentinel-2 AOT'],key='pollutant_select')
 if pollutant in ('NO₂','SO₂') and not pollutants.empty:
  token='no2' if pollutant=='NO₂' else 'so2'
  subset= pollutants[pollutants['product'].astype(str).str.lower().str.contains(token,na=False)]
  if city!='All cities':subset=subset[subset.city.eq(city)]
  st.dataframe(subset,hide_index=True,width='stretch')
  if 'column_mol_m2' in subset and subset.column_mol_m2.notna().any():st.bar_chart(subset.groupby('city').column_mol_m2.median())
 elif pollutant=='UV aerosol index':
  for place in (['Jacksonville','Detroit','Rochester'] if city=='All cities' else [city]):
   f=read(RES/f'atmosphere/{place.lower()}_aer_ai.csv')
   if not f.empty:st.write(place);st.dataframe(f,hide_index=True,width='stretch')
 elif pollutant=='Sentinel-2 AOT' and not aot.empty:st.dataframe(aot if city=='All cities' else aot[aot.city.eq(city)],hide_index=True,width='stretch')
 st.subheader('Nearest Sentinel-5P NO₂ and SO₂ columns at US registry sites')
 st.caption('QA-filtered nearest pixel center within 15 km. Multi-kilometre atmospheric columns in mol/m² are neither ground concentrations nor factory emissions.')
 if not pollutants.empty:
  subset=pollutants if city=='All cities' else pollutants[pollutants.city.eq(city)]
  chosen=subset[subset.facility_id.eq(str(selected))]
  if not chosen.empty:st.dataframe(chosen[['product','date','column_mol_m2','nearest_pixel_center_km','qa','status']],hide_index=True,width='stretch')
  st.dataframe(subset[['city','name','product','date','column_mol_m2','nearest_pixel_center_km','qa','status']],hide_index=True,width='stretch')
 else:st.info('Run python -m src.site_pollutants.')
 st.subheader('Coarse methane column and UV aerosol index')
 st.caption('Sentinel-5P/TROPOMI values are QA-filtered regional column observations within 50 km for CH4 and 30 km for aerosol index, several kilometres per pixel. Missing means no QA-valid observation, not zero methane or aerosol. Neither product attributes a source.')
 cities=sorted(factories.city.unique()) if city=='All cities' else [city]
 for location in cities:
  for product,title in [('ch4','CH4 XCH4 (ppb)'),('aer_ai','UV aerosol index (dimensionless)')]:
   data=read(RES/f'atmosphere/{location.lower()}_{product}.csv')
   if data.empty:st.info(f'{location}: {title} processing has not produced a table yet.');continue
   st.write(f'**{location}: {title}**')
   st.dataframe(data[['date','n_valid','median','p95','nearest_valid_km','status']],hide_index=True,width='stretch')
   valid=data.dropna(subset=['median'])
   if not valid.empty:st.line_chart(valid.assign(date=pd.to_datetime(valid.date)).set_index('date')[['median']])
 st.subheader('Sentinel-2 AOT contrasts')
 if not aot.empty:
  subset=aot if city=='All cities' else aot[aot.city.eq(city)]
  st.dataframe(subset[['city','name','date','near_aot','reference_aot','difference','downwind_minus_upwind','wind_speed_kmh']],hide_index=True,width='stretch')
 else:st.info('No valid AOT comparisons yet.')
 st.subheader('Regional CAMS model estimates')
 if not air.empty:
  subset=air if city=='All cities' else air[air.city.eq(city)]
  st.dataframe(subset.groupby('city')[['nitrogen_dioxide','sulphur_dioxide']].mean().round(2),width='stretch')
  if city!='All cities':st.line_chart(subset.assign(time=pd.to_datetime(subset.time)).set_index('time')[['nitrogen_dioxide','sulphur_dioxide']])
with esg_tab:
 st.subheader('ERA5 10 m wind')
 if not wind.empty:
  subset=wind if city=='All cities' else wind[wind.city.eq(city)]
  st.dataframe(subset.groupby('city')[['wind_speed_10m','wind_direction_10m']].mean().round(1),width='stretch')
  if city!='All cities':st.line_chart(subset.assign(time=pd.to_datetime(subset.time)).set_index('time')[['wind_speed_10m']])
 st.subheader('Scope 1/2 carbon accounting')
 carbon=read(RES/'carbon/scope1_scope2_by_period.csv')
 if not carbon.empty:
  st.dataframe(carbon,hide_index=True,width='stretch')
  st.bar_chart(carbon.set_index('facility_id')[['scope1_tco2e','scope2_tco2e']])
 else:st.info('No facility activity and factor ledger supplied. Fill data/facility_activity_template.csv, save as data/facility_activity.csv, then run python -m src.carbon_results. Satellite plume kg/h is not an annual inventory.')
 st.subheader('ESG evidence readiness')
 report=(RES/'esg_gri305_evidence.md').read_text() if (RES/'esg_gri305_evidence.md').exists() else 'Run python -m src.gri_report.'
 st.markdown(report)
 st.download_button('Download evidence report',report,'ecoorbit_gri305_evidence.md',mime='text/markdown')
with chat_tab:
 st.subheader('EcoOrbit Chat')
 st.caption('Explainable assistant for this PoC. It answers from bundled EcoOrbit results, methods and documentation. Off-topic questions are declined. Every other tab works without an API key.')
 env_key=_env_gemini_key()
 pasted=st.text_input('Gemini API key',value='',type='password',key='eo_key_box',help='Paste a key from Google AI Studio. Optional if GEMINI_API_KEY is already set. The key stays in this session and is not written to disk.')
 api_key=pasted.strip() or env_key
 if pasted.strip(): st.success('API key accepted for this browser session. It is not saved in the project.')
 elif env_key: st.success('Using GEMINI_API_KEY from the environment. Paste a different key above to override it.')
 else:
  st.info('The dashboard is fully usable without a key. Chat stays off until you paste a Gemini API key above or set GEMINI_API_KEY. Create a free key at https://aistudio.google.com/apikey')
 picked=''
 with st.expander('Starter questions',expanded=True):
  for question in CHAT_STARTERS:
   if st.button(question,use_container_width=True): picked=question
 if 'eo_messages' not in st.session_state: st.session_state.eo_messages=[]
 if st.session_state.eo_messages and st.button('Clear chat'):
  st.session_state.eo_messages=[]
  st.rerun()
 for message in st.session_state.eo_messages:
  with st.chat_message(message['role']): st.markdown(message['content'])
 prompt=picked or st.chat_input('Ask about EcoOrbit results, methods, or limits')
 if prompt:
  if not api_key:
   st.warning('Add a Gemini API key above, or set GEMINI_API_KEY, to use EcoOrbit Chat. The rest of the app does not need a key.')
  else:
   st.session_state.eo_messages.append({'role':'user','content':prompt})
   with st.chat_message('user'): st.markdown(prompt)
   with st.chat_message('assistant'):
    try:
     with st.spinner('Looking through EcoOrbit evidence...'):
      answer=_gemini_answer(api_key,prompt,st.session_state.eo_messages[:-1])
    except ImportError:
     answer='Install project requirements including google-genai (`python -m pip install -r requirements.txt`), then restart Streamlit. Other tabs do not need this package to display results.'
    except Exception as err:
     answer='Chat could not reach Gemini. The rest of EcoOrbit is unaffected. Check the API key and try again.\n\n'+str(err)[:500]
    st.markdown(answer)
   st.session_state.eo_messages.append({'role':'assistant','content':answer})

"""QA-screened TROPOMI NO2/SO2 columns near registry coordinates.

A nearest pixel center is only a geographic association. The pixel can contain
multiple industrial and nonindustrial sources; do not assign an emission rate.
"""
import argparse
import math
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import planetary_computer as pc
from pystac_client import Client

from src.atmosphere import DATES, STAC, download_asset

FIELDS = {
    'no2': ('nitrogendioxide_tropospheric_column', 0.75),
    'so2': ('sulfurdioxide_total_vertical_column', 0.50),
}
COLUMNS = ['city', 'facility_id', 'name', 'date', 'product', 'scene_id',
           'nearest_pixel_center_km', 'pixel_center_lat', 'pixel_center_lon',
           'column_mol_m2', 'qa', 'qa_min', 'variable', 'status']


def extract(path, sites, product, scene_id, date, max_distance_km=15):
    """Return nearest QA-valid cell per point, retaining its center and distance."""
    field, minimum = FIELDS[product]
    with h5py.File(path) as h:
        group = h['PRODUCT']
        lat = np.asarray(group['latitude'][0])
        lon = np.asarray(group['longitude'][0])
        values = np.asarray(group[field][0])
        qa_band = group['qa_value']
        scale = float(np.asarray(qa_band.attrs.get('scale_factor', 1)).ravel()[0])
        qa = np.asarray(qa_band[0], dtype='float32') * scale
        good = np.isfinite(values) & (np.abs(values) < 1e20) & (qa > minimum)
        rows = []
        for _, site in sites.iterrows():
            distance = np.hypot((lat-site.latitude)*111.1,
                (lon-site.longitude)*111.1*math.cos(math.radians(site.latitude)))
            nearest = int(np.argmin(np.where(good, distance, np.inf))) if good.any() else None
            km = float(distance.flat[nearest]) if nearest is not None else None
            matched = km is not None and km <= max_distance_km
            rows.append(dict(city=site.city, facility_id=site.facility_id,
                name=site['name'], date=date, product=product, scene_id=scene_id,
                nearest_pixel_center_km=km,
                pixel_center_lat=float(lat.flat[nearest]) if matched else None,
                pixel_center_lon=float(lon.flat[nearest]) if matched else None,
                column_mol_m2=float(values.flat[nearest]) if matched else None,
                qa=float(qa.flat[nearest]) if matched else None, qa_min=minimum,
                variable=field,
                status='coarse column pixel; no source attribution' if matched
                       else 'no QA-valid pixel center within 15 km'))
        return rows


def unavailable(sites, product, date, status):
    field, minimum = FIELDS[product]
    return [dict(city=s.city, facility_id=s.facility_id, name=s['name'],
        date=date, product=product, scene_id='', nearest_pixel_center_km=None,
        pixel_center_lat=None, pixel_center_lon=None, column_mol_m2=None,
        qa=None, qa_min=minimum, variable=field, status=status)
        for _, s in sites.iterrows()]


def analyze(registry='data/training_sites.csv', out='results/real/pollutants',
            cache='data/cache', max_days=1, cities=None, products=None):
    sites = pd.read_csv(registry, dtype={'facility_id': str})
    sites = sites[sites.label.eq(1)]
    selected_cities = list(cities or sorted(sites.city.unique()))
    selected_products = list(products or FIELDS)
    output = Path(out) / 'site_no2_so2.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = pd.read_csv(output, dtype={'facility_id': str}) if output.exists() else pd.DataFrame(columns=COLUMNS)
    catalog = Client.open(STAC)
    for city in selected_cities:
        group = sites[sites.city.eq(city)]
        if group.empty:
            raise ValueError(f'No industrial training sites for {city}')
        bbox = [group.longitude.min()-.1, group.latitude.min()-.1,
                group.longitude.max()+.1, group.latitude.max()+.1]
        for product in selected_products:
            if product not in FIELDS:
                raise ValueError(f'Unknown product {product}')
            items = list(catalog.search(collections=['sentinel-5p-l2-netcdf'],
                bbox=bbox, datetime=DATES[city],
                query={'s5p:product_name': {'eq': product}}, max_items=60).items())
            by_day = {}
            for item in items:
                by_day.setdefault(item.datetime.date().isoformat(), item)
            rows = []
            if not by_day:
                rows = unavailable(group, product, DATES[city],
                                   'no catalog item in image-week window')
            for day, item in list(sorted(by_day.items()))[:max_days]:
                try:
                    asset = pc.sign(item).assets[product]
                    local = download_asset(asset.href, Path(cache)/f'{item.id}.nc')
                    rows.extend(extract(local, group, product, item.id, day))
                except (OSError, KeyError, ValueError) as exc:
                    rows.extend(unavailable(group, product, day,
                        f'download or extraction failed: {type(exc).__name__}'))
                    print(city, product, day, type(exc).__name__, str(exc)[:120], flush=True)
                else:
                    print(city, product, day, 'sites', len(group), flush=True)
            # Replace only the requested city/product; retain completed other cities.
            existing = existing[~(existing.city.eq(city) & existing['product'].eq(product))]
            existing = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
            existing[COLUMNS].to_csv(output, index=False)
    return existing[COLUMNS]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--city', choices=list(DATES), help='Resume just one city')
    parser.add_argument('--product', choices=list(FIELDS), help='Resume NO2 or SO2 only')
    parser.add_argument('--max-days', type=int, default=1)
    args = parser.parse_args()
    result = analyze(cities=[args.city] if args.city else None,
                     products=[args.product] if args.product else None,
                     max_days=args.max_days)
    print(result.groupby(['city','product','status']).size())

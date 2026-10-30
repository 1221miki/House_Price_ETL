"""
Generate professional charts/visualizations from PostgreSQL data.
Outputs PNG files to Data/processed/charts/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config.database import get_db_engine

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Data', 'processed', 'charts')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BOROUGH_COLORS = {
    'Manhattan':    '#e94560',
    'Brooklyn':     '#0f3460',
    'Queens':       '#533483',
    'Bronx':        '#2d6a4f',
    'Staten Island':'#f4a261',
}
PALETTE = ['#e94560','#0f3460','#533483','#2d6a4f','#f4a261','#16213e','#1a1a2e']

DARK = {
    'figure.facecolor': '#0d1117',
    'axes.facecolor':   '#161b22',
    'axes.edgecolor':   '#30363d',
    'axes.labelcolor':  '#e6edf3',
    'xtick.color':      '#e6edf3',
    'ytick.color':      '#e6edf3',
    'text.color':       '#e6edf3',
    'grid.color':       '#21262d',
    'grid.linestyle':   '--',
    'grid.alpha':       0.5,
    'font.family':      'DejaVu Sans',
}
plt.rcParams.update(DARK)


# ─── Chart 1: Borough Average Price ───────────────────────────────────────────
def chart1_borough_avg_price(engine):
    df = pd.read_sql("""
        SELECT borough,
               ROUND(AVG(sale_price::numeric),0) AS avg_price,
               COUNT(*) AS total_sales
        FROM sale_events
        WHERE sale_price IS NOT NULL
          AND sale_price::numeric > 10000
          AND borough IS NOT NULL
        GROUP BY borough
        ORDER BY avg_price DESC
    """, engine)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [BOROUGH_COLORS.get(b, '#888') for b in df['borough']]
    bars = ax.bar(df['borough'], df['avg_price'], color=colors, edgecolor='#30363d', linewidth=0.8)

    for bar, val, cnt in zip(bars, df['avg_price'], df['total_sales']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 25000,
                f'${val/1e6:.2f}M', ha='center', va='bottom', fontsize=10,
                color='#e6edf3', fontweight='bold')
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                f'{cnt:,}\nsales', ha='center', va='center', fontsize=8,
                color='white', alpha=0.85)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'${x/1e6:.1f}M'))
    ax.set_title('Average Sale Price by NYC Borough', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Borough', fontsize=12)
    ax.set_ylabel('Average Sale Price (USD)', fontsize=12)
    ax.grid(axis='y', alpha=0.4); ax.set_axisbelow(True)
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'chart1_borough_avg_price.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  Saved: {path}')
    return path


# ─── Chart 2: Price Trend 2015-2025 ───────────────────────────────────────────
def chart2_price_trend(engine):
    df = pd.read_sql("""
        SELECT borough, sale_year,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price::numeric) AS median_price
        FROM sale_events
        WHERE sale_price IS NOT NULL
          AND sale_price::numeric > 10000
          AND sale_year BETWEEN 2015 AND 2025
          AND borough IN ('Manhattan','Brooklyn','Queens','Bronx','Staten Island')
        GROUP BY borough, sale_year
        ORDER BY sale_year, borough
    """, engine)

    fig, ax = plt.subplots(figsize=(12, 6))
    for bor, grp in df.groupby('borough'):
        color = BOROUGH_COLORS.get(bor, '#aaa')
        ax.plot(grp['sale_year'], grp['median_price'], marker='o', linewidth=2.5,
                markersize=6, label=bor, color=color)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'${x/1e3:.0f}K'))
    ax.set_title('Median Sale Price Trend 2015-2025 by Borough', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Median Sale Price (USD)', fontsize=12)
    ax.legend(loc='upper left', framealpha=0.3, fontsize=10)
    ax.grid(alpha=0.4)
    ax.set_xticks(range(2015, 2026))
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'chart2_price_trend.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  Saved: {path}')
    return path


# ─── Chart 3: Property Type ────────────────────────────────────────────────────
def chart3_property_type(engine):
    df = pd.read_sql("""
        SELECT property_type,
               total_sales,
               ROUND(avg_sale_price::numeric, 0) AS avg_price
        FROM v_property_type_performance
        WHERE property_type != 'unclassified'
        ORDER BY total_sales DESC
        LIMIT 7
    """, engine)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    labels = [t.replace('_', ' ').title() for t in df['property_type']]
    colors = PALETTE[:len(df)]

    bars = ax1.barh(labels, df['total_sales'], color=colors, edgecolor='#30363d')
    for bar, val in zip(bars, df['total_sales']):
        ax1.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                 f'{val:,}', va='center', fontsize=9, color='#e6edf3')
    ax1.set_title('Sales Volume by Property Type', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Number of Sales', fontsize=11)
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'{int(x):,}'))
    ax1.grid(axis='x', alpha=0.4); ax1.invert_yaxis()

    bars2 = ax2.barh(labels, df['avg_price'], color=colors, edgecolor='#30363d')
    for bar, val in zip(bars2, df['avg_price']):
        ax2.text(bar.get_width() + 50000, bar.get_y() + bar.get_height()/2,
                 f'${val/1e6:.1f}M', va='center', fontsize=9, color='#e6edf3')
    ax2.set_title('Avg Sale Price by Property Type', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Average Sale Price (USD)', fontsize=11)
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'${x/1e6:.0f}M'))
    ax2.grid(axis='x', alpha=0.4); ax2.invert_yaxis()

    fig.suptitle('NYC Property Type Analysis', fontsize=16, fontweight='bold', y=1.01)
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'chart3_property_type.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  Saved: {path}')
    return path


# ─── Chart 4: Top Zip Codes ────────────────────────────────────────────────────
def chart4_top_zipcodes(engine):
    df = pd.read_sql("""
        SELECT zip_code, borough,
               ROUND(AVG(price_per_sqft::numeric),0) AS avg_ppsf,
               COUNT(*) AS sales
        FROM sale_events
        WHERE price_per_sqft IS NOT NULL
          AND price_per_sqft::numeric > 0
          AND price_per_sqft::numeric < 10000
          AND zip_code IS NOT NULL AND zip_code != ''
        GROUP BY zip_code, borough
        HAVING COUNT(*) > 100
        ORDER BY avg_ppsf DESC
        LIMIT 10
    """, engine)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [BOROUGH_COLORS.get(b, '#888') for b in df['borough']]
    bars = ax.bar(df['zip_code'].astype(str), df['avg_ppsf'], color=colors, edgecolor='#30363d')

    for bar, val, bor in zip(bars, df['avg_ppsf'], df['borough']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                f'${val:,.0f}', ha='center', va='bottom', fontsize=9,
                color='#e6edf3', fontweight='bold')
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                bor[:3], ha='center', va='center', fontsize=7.5,
                color='white', alpha=0.9, rotation=90)

    ax.set_title('Top 10 NYC Zip Codes by Price per Sq Ft', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Zip Code', fontsize=12)
    ax.set_ylabel('Avg Price per Sq Ft (USD)', fontsize=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'${x:,.0f}'))
    ax.grid(axis='y', alpha=0.4); ax.set_axisbelow(True)
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'chart4_top_zipcodes.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  Saved: {path}')
    return path


# ─── Chart 5: ETL Summary Infographic ─────────────────────────────────────────
def chart5_etl_pipeline(engine):
    prop_count = pd.read_sql("SELECT COUNT(*) AS c FROM properties", engine).iloc[0]['c']
    sale_count = pd.read_sql("SELECT COUNT(*) AS c FROM sale_events", engine).iloc[0]['c']
    idx_count  = pd.read_sql(
        "SELECT COUNT(*) AS c FROM pg_indexes WHERE schemaname='public'", engine
    ).iloc[0]['c']

    fig, axes = plt.subplots(1, 4, figsize=(14, 5))
    fig.suptitle('NYC House Price ETL — Pipeline Summary', fontsize=16, fontweight='bold', y=1.02)

    stats = [
        ('7,009,514',              'Raw Records\nExtracted',  '#e94560'),
        (f'{prop_count+sale_count:,}', 'Records\nLoaded to DB', '#0f3460'),
        (f'{idx_count}',           'Database\nIndexes',       '#533483'),
        ('4',                      'Analytical\nSQL Views',   '#2d6a4f'),
    ]

    for ax, (val, label, color) in zip(axes, stats):
        ax.set_facecolor(color)
        ax.text(0.5, 0.60, val,   ha='center', va='center', fontsize=22,
                fontweight='bold', color='white', transform=ax.transAxes)
        ax.text(0.5, 0.25, label, ha='center', va='center', fontsize=12,
                color='white', alpha=0.9, transform=ax.transAxes)
        ax.axis('off')

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'chart5_etl_summary.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    print(f'  Saved: {path}')
    return path


if __name__ == '__main__':
    print('Connecting to PostgreSQL...')
    engine = get_db_engine()
    print('Generating charts...\n')

    paths = []
    paths.append(chart1_borough_avg_price(engine))
    paths.append(chart2_price_trend(engine))
    paths.append(chart3_property_type(engine))
    paths.append(chart4_top_zipcodes(engine))
    paths.append(chart5_etl_pipeline(engine))

    print(f'\nDone! {len(paths)} charts saved to: Data/processed/charts/')
    for p in paths:
        print(f'  {os.path.basename(p)}')

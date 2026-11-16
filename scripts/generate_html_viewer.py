import pandas as pd
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

df_prop = pd.read_csv(ROOT_DIR / 'Data' / 'properties_preview.csv').fillna('')
df_sales = pd.read_csv(ROOT_DIR / 'Data' / 'sale_events_preview.csv').fillna('')

# Select the most interesting columns for a clean visual experience
prop_selected_cols = ['record_id', 'parcel_id', 'address_line', 'city', 'state', 'zip_code', 'property_type', 'building_sqft', 'year_built', 'assessed_value', 'market_value']
sales_selected_cols = ['sale_id', 'parcel_id', 'address_line', 'city', 'state', 'zip_code', 'sale_price', 'sale_date', 'deed_type', 'building_sqft', 'year_built']

prop_cols = [{'title': c, 'data': c} for c in prop_selected_cols if c in df_prop.columns]
sales_cols = [{'title': c, 'data': c} for c in sales_selected_cols if c in df_sales.columns]

prop_data = df_prop[[c['data'] for c in prop_cols]].to_dict(orient='records')
sales_data = df_sales[[c['data'] for c in sales_cols]].to_dict(orient='records')

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NYC Real Estate House Price ETL | Project Explorer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
    <style>
        :root {{
            color-scheme: light;
            --ink: #12243a;
            --muted: #64748b;
            --brand: #0f766e;
            --brand-dark: #115e59;
            --line: #e2e8f0;
            --surface: #ffffff;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 28px;
            background: #f3f6f8;
            color: var(--ink);
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .container-fluid {{ max-width: 1240px; }}
        .hero {{
            position: relative;
            overflow: hidden;
            padding: clamp(28px, 5vw, 58px);
            border-radius: 24px;
            background: radial-gradient(circle at 88% 18%, rgba(45, 212, 191, .22), transparent 28%), linear-gradient(125deg, #10243b, #173b4c 72%, #155e63);
            color: #fff;
            box-shadow: 0 18px 45px rgba(15, 41, 58, .16);
        }}
        .hero-kicker, .section-kicker {{
            color: #5eead4;
            font-size: .75rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }}
        .hero h1 {{
            max-width: 760px;
            margin: 14px 0;
            font-size: clamp(2.2rem, 5vw, 4.1rem);
            font-weight: 800;
            letter-spacing: -.045em;
            line-height: 1.04;
        }}
        .hero-copy {{ max-width: 690px; color: #d3e2e8; font-size: 1.05rem; line-height: 1.75; }}
        .hero-actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 26px; }}
        .hero-actions a {{
            display: inline-flex;
            align-items: center;
            min-height: 44px;
            padding: 10px 17px;
            border: 1px solid rgba(255,255,255,.32);
            border-radius: 999px;
            color: #fff;
            font-weight: 700;
            text-decoration: none;
            transition: transform .18s ease, background .18s ease;
        }}
        .hero-actions a:first-child {{ border-color: #5eead4; background: #5eead4; color: #103344; }}
        .hero-actions a:hover {{ transform: translateY(-1px); }}
        .hero-note {{ margin: 22px 0 0; color: #bed0d9; font-size: .88rem; }}
        .stats-grid, .pipeline-grid, .language-grid {{ display: grid; gap: 14px; }}
        .stats-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 18px 0 48px; }}
        .stat-card, .section-card {{
            border: 1px solid var(--line);
            border-radius: 18px;
            background: var(--surface);
            box-shadow: 0 8px 24px rgba(15, 23, 42, .035);
        }}
        .stat-card {{ padding: 20px; }}
        .stat-value {{ display: block; color: var(--brand-dark); font-size: clamp(1.45rem, 3vw, 2rem); font-weight: 800; letter-spacing: -.04em; }}
        .stat-label {{ display: block; margin-top: 6px; color: var(--muted); font-size: .9rem; }}
        .section {{ margin: 46px 0; scroll-margin-top: 20px; }}
        .section-heading {{ margin-bottom: 20px; }}
        .section-kicker {{ color: var(--brand); }}
        .section-heading h2 {{ margin: 8px 0; color: var(--ink); font-size: clamp(1.6rem, 3vw, 2.3rem); font-weight: 800; letter-spacing: -.035em; }}
        .section-heading p {{ max-width: 760px; margin: 0; color: var(--muted); line-height: 1.7; }}
        .pipeline-grid {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
        .pipeline-step, .language-card {{ padding: 21px; }}
        .step-number {{
            display: inline-grid;
            width: 34px;
            height: 34px;
            place-items: center;
            border-radius: 11px;
            background: #ccfbf1;
            color: #115e59;
            font-weight: 800;
        }}
        .pipeline-step h3, .language-card h3 {{ margin: 16px 0 8px; font-size: 1.05rem; font-weight: 800; }}
        .pipeline-step p, .language-card p {{ margin: 0; color: var(--muted); font-size: .91rem; line-height: 1.65; }}
        .language-grid {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
        .language-mark {{
            display: inline-grid;
            min-width: 46px;
            height: 42px;
            padding: 0 8px;
            place-items: center;
            border-radius: 12px;
            background: #ecfeff;
            color: #0f766e;
            font-size: .82rem;
            font-weight: 900;
        }}
        .language-card small {{ display: block; margin-top: 12px; color: #475569; line-height: 1.55; }}
        .data-card {{ padding: clamp(16px, 3vw, 28px); }}
        .data-note {{
            margin: 0 0 18px;
            padding: 13px 15px;
            border-left: 4px solid #0f766e;
            border-radius: 8px;
            background: #f0fdfa;
            color: #335b5b;
            font-size: .9rem;
            line-height: 1.6;
        }}
        .nav-pills {{ gap: 8px; }}
        .nav-pills .nav-link {{ border-radius: 999px; color: #475569; font-weight: 700; }}
        .nav-pills .nav-link.active {{ background: var(--brand); }}
        .nav-link {{ font-size: .93rem; }}
        table.dataTable {{ font-size: 13px; }}
        table.dataTable thead th {{ white-space: nowrap; }}
        .team-card {{ padding: 22px; }}
        .team-list {{ display: flex; flex-wrap: wrap; gap: 10px; padding: 0; list-style: none; }}
        .team-list li {{ padding: 9px 13px; border: 1px solid var(--line); border-radius: 999px; background: #fff; color: #334155; font-size: .88rem; }}
        footer {{ padding: 20px 0 8px; color: var(--muted); font-size: .85rem; text-align: center; }}
        @media (max-width: 900px) {{
            .pipeline-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .language-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .stats-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        }}
        @media (max-width: 560px) {{
            body {{ padding: 14px; }}
            .stats-grid, .pipeline-grid, .language-grid {{ grid-template-columns: 1fr; }}
            .hero {{ border-radius: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <header class="hero" id="overview">
            <span class="hero-kicker">House Price ETL - NYC data project</span>
            <h1>From city records to real-estate insight.</h1>
            <p class="hero-copy">A practical data pipeline that turns property and sale records into clean, validated information for analysis. Explore sample rows, see how each ETL stage works, and learn what every language does in this project.</p>
            <nav class="hero-actions" aria-label="Page sections">
                <a href="#datasets">Explore sample data</a>
                <a href="#workflow">Understand the workflow</a>
                <a href="#languages">Languages explained</a>
            </nav>
            <p class="hero-note">The tables below show small preview files for a quick browser demo; they are not the full source datasets.</p>
        </header>

        <section class="stats-grid" aria-label="Dataset summary">
            <article class="stat-card"><span class="stat-value">3,306,420</span><span class="stat-label">property records in the source dataset</span></article>
            <article class="stat-card"><span class="stat-value">3,703,094</span><span class="stat-label">sale records in the source dataset</span></article>
            <article class="stat-card"><span class="stat-value">7,009,514</span><span class="stat-label">combined source records</span></article>
            <article class="stat-card"><span class="stat-value">1-to-many</span><span class="stat-label">properties can relate to multiple sales</span></article>
        </section>

        <section class="section" id="workflow">
            <div class="section-heading">
                <span class="section-kicker">How it works</span>
                <h2>One clear path from raw files to useful analysis</h2>
                <p>ETL means Extract, Transform, Load. Each step has one job, making data easier to check, maintain, and explain.</p>
            </div>
            <div class="pipeline-grid">
                <article class="section-card pipeline-step"><span class="step-number">01</span><h3>Extract</h3><p>PyArrow reads Parquet files in batches, so the pipeline can process large data without loading everything into memory at once.</p></article>
                <article class="section-card pipeline-step"><span class="step-number">02</span><h3>Transform</h3><p>Pandas cleans columns, standardizes parcel IDs, and prepares useful values such as sale year and price per square foot.</p></article>
                <article class="section-card pipeline-step"><span class="step-number">03</span><h3>Validate</h3><p>Rules check required IDs, valid dates, positive sale prices, and reasonable property measurements before loading.</p></article>
                <article class="section-card pipeline-step"><span class="step-number">04</span><h3>Load</h3><p>SQLAlchemy and PostgreSQL store the validated property and sale records in related database tables.</p></article>
                <article class="section-card pipeline-step"><span class="step-number">05</span><h3>Analyze</h3><p>SQL views and queries summarize markets, prices, and property trends for reports and business decisions.</p></article>
            </div>
        </section>

        <section class="section" id="languages">
            <div class="section-heading">
                <span class="section-kicker">The technology, in plain language</span>
                <h2>Languages used in this project</h2>
                <p>Languages describe the instructions and structure; libraries and tools provide specialized features such as reading Parquet files or connecting to a database.</p>
            </div>
            <div class="language-grid">
                <article class="section-card language-card"><span class="language-mark">Py</span><h3>Python</h3><p>The main programming language for the ETL pipeline and project scripts.</p><small>Used for extracting data, cleaning it with Pandas, validating records, loading the database, and running tests.</small></article>
                <article class="section-card language-card"><span class="language-mark">SQL</span><h3>SQL</h3><p>The language for working with relational databases.</p><small>Used to define PostgreSQL tables and constraints, and to create views and queries for analysis.</small></article>
                <article class="section-card language-card"><span class="language-mark">HTML</span><h3>HTML</h3><p>The structure and content of this webpage.</p><small>It defines headings, sections, links, dataset tables, and labels so browsers know what each part means.</small></article>
                <article class="section-card language-card"><span class="language-mark">CSS</span><h3>CSS</h3><p>The visual design rules for the webpage.</p><small>It controls colors, spacing, typography, cards, and layouts that adapt to phones and larger screens.</small></article>
                <article class="section-card language-card"><span class="language-mark">JS</span><h3>JavaScript</h3><p>The behavior that makes the webpage interactive.</p><small>It powers searchable, sortable, paginated preview tables and the property/sales tabs.</small></article>
            </div>
        </section>

        <section class="section" id="datasets">
            <div class="section-heading">
                <span class="section-kicker">Explore the data</span>
                <h2>Property and sale-event previews</h2>
                <p>Search, sort, and page through the sample rows. The complete Parquet datasets are processed by the Python pipeline, not loaded into this browser page.</p>
            </div>
            <div class="section-card data-card">
                <p class="data-note"><strong>About these tables:</strong> The property dataset describes parcels and their physical or assessed characteristics. The sale-events dataset records transactions. A parcel can have multiple historical sale events.</p>
                <ul class="nav nav-pills mb-4" id="datasetTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="prop-tab" data-bs-toggle="pill" data-bs-target="#prop-pane" type="button" role="tab" aria-controls="prop-pane" aria-selected="true">
                        Properties <span class="badge text-bg-light ms-1" id="prop-preview-count">0</span>
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="sales-tab" data-bs-toggle="pill" data-bs-target="#sales-pane" type="button" role="tab" aria-controls="sales-pane" aria-selected="false">
                        Sale events <span class="badge text-bg-light ms-1" id="sales-preview-count">0</span>
                    </button>
                </li>
            </ul>

            <div class="tab-content" id="datasetTabsContent">
                <div class="tab-pane fade show active" id="prop-pane" role="tabpanel">
                    <div class="table-responsive">
                        <table id="propTable" class="table table-striped table-hover table-bordered w-100"></table>
                    </div>
                </div>
                <div class="tab-pane fade" id="sales-pane" role="tabpanel">
                    <div class="table-responsive">
                        <table id="salesTable" class="table table-striped table-hover table-bordered w-100"></table>
                    </div>
                </div>
            </div>
        </section>

        <section class="section" id="team">
            <div class="section-heading">
                <span class="section-kicker">Project contributors</span>
                <h2>Built by the project team</h2>
            </div>
            <div class="section-card team-card">
                <ul class="team-list">
                    <li>Asamnew Agiz - DBU1601394</li>
                    <li>Solomon Tadese - DBU1601626</li>
                    <li>Dagmawit Eshete - DBU1601878</li>
                    <li>Jemal Yimer - DBU1601836</li>
                    <li>Selamawit Tadese - 1601596</li>
                    <li>Ehitemelak Tekle Haymanot - 1602121</li>
                </ul>
            </div>
        </section>
        <footer>NYC Real Estate House Price ETL - Python, PostgreSQL, and interactive web technologies</footer>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
    <script>
        const propData = {json.dumps(prop_data)};
        const propCols = {json.dumps(prop_cols)};
        const salesData = {json.dumps(sales_data)};
        const salesCols = {json.dumps(sales_cols)};

        $(document).ready(function() {{
            $('#prop-preview-count').text(propData.length.toLocaleString() + ' preview rows');
            $('#sales-preview-count').text(salesData.length.toLocaleString() + ' preview rows');

            $('#propTable').DataTable({{
                data: propData,
                columns: propCols,
                pageLength: 10,
                scrollX: true
            }});

            $('#salesTable').DataTable({{
                data: salesData,
                columns: salesCols,
                pageLength: 10,
                scrollX: true
            }});
        }});
    </script>
</body>
</html>
'''

output_path = ROOT_DIR / 'dataset_viewer.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"[SUCCESS] Dataset viewer created at: {output_path}")


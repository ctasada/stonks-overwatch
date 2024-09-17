# Stocks Portfolio

## Start Developing

### With Docker
```shell
docker compose build
docker compose up
```

### Without Docker

Update Dependencies
```shell
poetry update
npm update
```

Install Dependencies
```shell
poetry install
poetry run src/manage.py npminstall
```

Run the server
```shell
poetry run src/manage.py runserver
open http://127.0.0.1:8000
```

Run Linter
```shell
poetry run ruff check
poetry run ruff format
```

Run Tests
```shell
poetry run pytest
```

Create Migrations
```shell
poetry run src/manage.py makemigrations degiro
```

Create Database
```shell
poetry run src/manage.py migrate
poetry run src/manage.py runscript init_db
```

## Documentation

* [DeGiro Connector](https://github.com/Chavithra/degiro-connector)
* [Bootstrap](https://getbootstrap.com)

## Dependencies

* https://www.npmjs.com/package/chroma-js

## Ideas

* [Django Jazzmin](https://github.com/farridav/django-jazzmin)
* [Django Bootstrap Tutorial](https://github.com/thalesbruno/django_bootstrap)
* [Django Bootstrap-4](https://github.com/zostera/django-bootstrap4)
* [Django Soft-UI Dashboard](https://appseed.us/product/django-soft-ui-dashboard)

## HowTos
* [Bootstrap Sidebar](https://bootstrapious.com/p/bootstrap-sidebar)
* [Mastering Multi-hued Color Scales with Chroma.js](https://www.vis4.net/blog/2013/09/mastering-multi-hued-color-scales/)

**Should we replace Django by Flask?**

## Other interesting projects
* https://github.com/leo-pfeiffer/portfolio_dashboard
* https://github.com/lucalaringe/degiro_portfolio_analytics
* https://app.portfoliodividendtracker.com/p/jongbeleggen?locale=en (Has some interesting diagrams and data)
* https://divvydiary.com/en/p/24094?tab=depot
* https://capitalyse.app/app/degiro/ -> Seems to have some errors, but data and graphs are interesting

## BUGS
- Dashboard: JNJ & JPM are associated with the wrong sector
- Portfolio is not updated on startup. A migration needs to be forced
- IBERDROLA Non-Tradable Dividends: Are properly calculated? Doesn't seem to calculate quantity properly
- When Login, connection needs to be recreated if int_account or user_token are not initially provided
- Import seems to create duplicated entries in Cash. Needs review and replication

## TODOs
- [ ] DeGiro Client: Stop using Totp and request 2FA for each connection
- [ ] Portfolio: Show filter to see Open/Close/All stocks
- [ ] Improve side-bar behaviour
- [ ] Replace dicts by properly designed models
- [ ] Provide support for both Unrealized and Realized Gain/Loss
        Onger. W/V € - Gain/Loss Unrealized - unrealizedPl
        Totale W/V € - Gain/Loss Total (Realized + unrealized) - totalPl
- [ ] Would be interesting to add filters to the Account Overview page and aggregate
- [ ] Add graph with Portfolio Cumulative P&L / Cumulative Net Contributions / Portfolio NAV (https://www.investopedia.com/terms/n/nav.asp)
- [ ] Check migration from ChartJS to https://plotly.com/javascript/ or https://recharts.org/ or https://d3js.org
- [ ] BUG: Calculated Cash Balance is 26 cents larger (see src/scripts/account_report.py)
- [ ] Track https://github.com/chartjs/Chart.js/issues/11005
- [ ] Review Portfolio growth. Indicates negative growth, which never really happened.
- [ ] Some stocks (mainly Spanish) don't have Sector or other data. Find workaround
- [ ] Fontawesome is replaceble by https://icons.getbootstrap.com

## Logos
- https://eodhd.com/financial-apis-blog/40000-company-logos (requires API Key)
- https://github.com/nvstly/icons (misses icons)
- https://github.com/ahmeterenodaci/Nasdaq-Stock-Exchange-including-Symbols-and-Logos?tab=readme-ov-file (misses many icons)
- https://data.nasdaq.com/databases/LOGO (requires Token)
- https://logos.stockanalysis.com/aapl.svg (misses some stocks)

# Portfolio Performance
- https://portfolioslab.com/tools/stock-comparison/AAPL/MSFT
- https://stonksfolio.com/portfolios/4qltYv/performance

# Libraries
- https://pypi.org/project/QuantStats/
- https://github.com/wilsonfreitas/awesome-quant?tab=readme-ov-file#python
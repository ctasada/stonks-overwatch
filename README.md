# Stonks Overwatch

**Stonks Overwatch** is a new Open Source Stocks Dashboard.

Why do we need yet another dashboard? I have been a DeGiro user for many years, and the more active I was, 
the more frustrated I became with the lack of any decent dashboard to overview my investments.

After trying different options (I will commit names) I couldn't find any that was really covering my needs, or 
that I could trust.

## What does offer **Stonks Overwatch**?

**Stonks Overwatch** is born with the intention to provide a usable investment dashboard for DeGiro, but with the desire
to keep growing to provide many more features in the future.

Right now the features we offer are:
* Realtime access to your DeGiro investments
* Portfolio value overtime
* Portfolio growth
* Dividends overview
* Fees overview
* Deposits overview
* Diversification overview
* Transactions
* Account Statements

## How to use **Stonks Overwatch**

I tried to make it as easy as possible to use, but some minimum technical knowledge is needed.

Checkout the repository in your computer
   `git clone ctasada/stonks-overwatch`

You can execute `make start`, it will install and configure everything needed to run.

Alternatively you can also use Docker
```shell
make docker-run
```

The application is available at [http://127.0.0.1:8000](http://127.0.0.1:8000) Simply open you browser in that URL.

### How to login to DeGiro?
You can login to DeGiro in two different ways

### Use the Login form
When you open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000) you will see a login form. Simply introduce
your credentials, including the OTP (One-Time-Password).

The first time, the application will retrieve all your portfolio from DeGiro and you are good to go

> Using this approach, no credentials are stored anywhere. You will need to repeat this step everytime  

### Automatic login
If you don't want to introduce your credentials everytime, it's possible to store them in a file, so login will be much
more comfortable and transparent.

Copy the file `config/config.json.template` to `config/config.json`

```json
{
    "degiro": {
        "credentials": {
            "username": "USERNAME",
            "password": "PASSWORD",
            "totp_secret_key": "See https://github.com/Chavithra/stonks_overwatch-connector#35-how-to-use-2fa-",
        },
        "base_currency": "EUR - Optional field. Uses DeGiro base currency by default",
        "start_date": "PORTFOLIO CREATION DATE. Defaults to 2020-01-01"
        "update_frequency_minutes": "How frequently the data from DeGiro should be updated. Defaults to 5 minutes"
    }
}
```
Only the `credentials` section is mandatory, put your credentials in the corresponding fields, and follow the instructions
to obtain your `totp_secret_key`. You can also skip it, and the application will ask for you OTP everytime.

## Start Developing

### With Docker
```shell
docker compose build
docker compose up
```

### Without Docker

Update Dependencies
```shell
poetry self update
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
poetry run src/manage.py makemigrations
```

Create Database
```shell
poetry run src/manage.py migrate
poetry run src/manage.py runscript init_db
```

Debugging & Profiling
```shell
make run profile=true debug=true
```
Passing the parameter `profile=true` will enable profiling, and `debug=true` will log in debugging mode

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
* https://github.com/lucalaringe/degiro_portfolio_analytics <<< CHECK!!!!
* https://github.com/CNugteren/DGPC
* https://app.portfoliodividendtracker.com/p/jongbeleggen?locale=en (Has some interesting diagrams and data)
* https://divvydiary.com/en/p/24094?tab=depot
* https://capitalyse.app/app/degiro/ -> Seems to have some errors, but data and graphs are interesting

## BUGS
- Dashboard: JNJ & JPM are associated with the wrong sector
- IBERDROLA Non-Tradable Dividends: Are properly calculated? Doesn't seem to calculate quantity properly
- Some stocks are no longer available in DeGiro. Need to find a way to handle them
    - 'ATVI'(350113856)
    - 'TYME'(600028575)
    - 'DPZ'(330187819): The symbol is available, but maybe the productId is not?
    - 'PLTR'(600121287): The symbol is available, but maybe the productId is not?
    - 'WEBR'(600179738): The symbol is available, but maybe the productId is not?
    - 'TEF.D'(280180545)
    - 'FRZA'(600236745)
    - 600179738: No chart found
- CreateProduct Quotation do not respect the proper timeframes
- Django Cache is disabled so that the portfolio selection works, otherwise the page is not properly reload
- Error loading Docker Image in MacOS Intel: 
  - "CPU features not detected: avx2"
  - use 'polars-lts-cpu' instead of 'polars' in Dockerfile
- Dashboard: Drawing the dashboard is slow. Seems that the code is executed three times
- Review Closed/All positions in Portfolio Overview. Some entries contain unexpected/inconsistent values
- TEAM: Growth values seem to be too low for what I remember, should be ~80%

## TODOs
- [ ] DeGiro Client: Stop using Totp and request 2FA for each connection
- [ ] Provide support for both Unrealized and Realized Gain/Loss
        Onger. W/V € - Gain/Loss Unrealized - unrealizedPl
        Totale W/V € - Gain/Loss Total (Realized + unrealized) - totalPl
- [ ] Would be interesting to add filters to the Account Overview page and aggregate
- [ ] Add graph with Portfolio Cumulative P&L / Cumulative Net Contributions / Portfolio NAV (https://www.investopedia.com/terms/n/nav.asp)
- [ ] Check migration from ChartJS to https://plotly.com/javascript/ or https://recharts.org/ or https://d3js.org
- [ ] Track https://github.com/chartjs/Chart.js/issues/11005
- [ ] Review Portfolio growth. Indicates negative growth, which never really happened.
- [ ] Some stocks (mainly Spanish) don't have Sector or other data. Find workaround
- [ ] Fontawesome is replaceable by https://icons.getbootstrap.com
- [ ] Provide more information in the Dashboard performance overview
- [ ] Migrate UI to https://github.com/coreui/coreui
- [ ] Add GitHub Dependabot support for Poetry: Track https://github.com/dependabot/dependabot-core/issues/11237
- [ ] Provide more details about Dividends per year
- [ ] Should include Dividends in the Deposit Overview?
- [ ] Disable Django Admin page by default
- [ ] Track delisted stocks
  - EODHD: https://eodhd.medium.com/leveraging-delisted-stocks-for-backtesting-a-3-ema-strategy-using-python-d67221e774f5
    - https://eodhd.com/pricing
  - Polygon.io: https://polygon.io/pricing (2 years free, rest paying)
  - Tiingo: https://www.tiingo.com/products/end-of-day-stock-price-data
    - https://www.tiingo.com/documentation/end-of-day
  - Alpaca: https://alpaca.markets

## Logos
- https://eodhd.com/financial-apis-blog/40000-company-logos (requires API Key)
- https://github.com/nvstly/icons (misses icons)
- https://github.com/ahmeterenodaci/Nasdaq-Stock-Exchange-including-Symbols-and-Logos?tab=readme-ov-file (misses many icons)
- https://data.nasdaq.com/databases/LOGO (requires Token)
- https://logos.stockanalysis.com/aapl.svg (misses some stocks)

# Portfolio Performance
- https://portfolioslab.com/tools/stock-comparison/AAPL/MSFT
- https://stonksfolio.com/portfolios/4qltYv/performance
- https://blog.quantinsti.com/portfolio-analysis-performance-measurement-evaluation/

* TWRR focuses purely on the timing of cash flows, providing an accurate measure of performance that disregards the 
  amount of money involved.
* XIRR, on the other hand, considers both the timing and the size of cash flows, offering a complete picture of 
  investment returns.

# Libraries
- https://pypi.org/project/QuantStats/
- https://github.com/wilsonfreitas/awesome-quant?tab=readme-ov-file#python
- https://github.com/robertmartin8/PyPortfolioOpt
- https://pypi.org/project/pyxirr/

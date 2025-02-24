# Stonks Overwatch

**Stonks Overwatch** is a new Open Source Stocks Dashboard.

Why do we need yet another dashboard? I have been a DEGIRO user for many years, and the more active I was,
the more frustrated I became with the lack of any decent dashboard to overview my investments.

After trying different options (I will omit names), I couldn't find any that was really covering my needs, or
that I could trust.

Stonks Overwatch runs locally and doesn't share your data with anyone. Your data is yours.

## What does offer **Stonks Overwatch**?

**Stonks Overwatch** is born with the intention to provide a usable investment dashboard for DEGIRO, but with the desire
to keep growing to provide many more features in the future.

Right now the features we offer are:

* Realtime access to your DEGIRO investments
* Portfolio value overtime
* Portfolio growth
* Dividends overview
* Fees overview
* Deposits overview
* Diversification overview
* Transactions
* Account Statements

### How to login to DEGIRO

See [Wiki - DEGIRO](./docs/DEGIRO)

### How to login to Bitvavo

See [Wiki - Bitvavo](./docs/Bitvavo)

### How to login to IBKR (Interactive Brokers)

See [Wiki - IBKR](https://github.com/ctasada/stonks-overwatch/wiki/IBKR)

## Start Developing

See [Wiki - Developing Stonks Overwatch](./docs/Developing-Stonks-Overwatch)

## Documentation

* [DEGIRO Connector](https://github.com/Chavithra/degiro-connector)
* [IBKR Client](https://github.com/Voyz/ibind)
* [Bootstrap](https://getbootstrap.com)

## Other interesting projects

* "https://github.com/leo-pfeiffer/portfolio_dashboard"
* "https://github.com/lucalaringe/degiro_portfolio_analytics" <<< CHECK!!!!
* "https://github.com/CNugteren/DGPC"
* [Portfolio Dividend Tracker](https://app.portfoliodividendtracker.com/p/jongbeleggen?locale=en) (Has some interesting diagrams and data)
* [DivvyDiary](https://divvydiary.com/en/p/24094?tab=depot)
* [Capitalyse](https://capitalyse.app/app/degiro/) → Seems to have some errors, but data and graphs are interesting
* [Giroscope](https://giroscope.io) → Seems to have some errors, but data and graphs are interesting

## BUGS

* IBERDROLA Non-Tradable Dividends: Are properly calculated? Doesn't seem to calculate quantity properly
* Some stocks are no longer available in DEGIRO. We Need to find a way to handle them
  * 'TYME'(600028575)
  * 'WEBR'(600179738) (https://www.investing.com/equities/weber-chart)
  * 'TEF.D'(280180545)
  * 'FRZA'(600236745)
* CreateProduct Quotation does not respect the proper timeframes
* Django Cache is disabled so that the portfolio selection works, otherwise the page is not properly reload
* Dashboard: Drawing the dashboard is slow. It seems that the code is executed three times
* Review Closed/All positions in Portfolio Overview. Some entries contain unexpected/inconsistent values
* TEAM: Growth values seem too low for what I remember, should be ~80%
* Portfolio Growth drops to 0 when running in offline mode
* Portfolio Growth: Zoom works, but Panning doesn't work. Needs to be fixed

## TODOs

* [ ] Add information about the sectors. Maybe a tooltip in the places where sectors are used.
* [ ] Tables should allow choosing the number of rows to show.
* [ ] Portfolio Tables would be migrated to "http://bootstrap-table.com/"
* [ ] Review ALL BUGS and TODOs and move them to their corresponding Github issues
* [ ] Replace all the Tables with "https://bootstrap-table.com"
* [ ] Evaluate the migration from Poetry to Uv
* [ ] DEGIRO Client: Stop using Totp and request 2FA for each connection
* [ ] Provide support for both Unrealized and Realized Gain/Loss
  * Onger. W/V € - Gain/Loss Unrealized - unrealizedPl
  * Totale W/V € - Gain/Loss Total (Realized + unrealized) - totalPl
* [ ] It would be interesting to add filters to the Account Overview page and aggregate
* [ ] Add the graph with Portfolio Cumulative P&L / Cumulative Net Contributions / Portfolio NAV (https://www.investopedia.com/terms/n/nav.asp)
* [ ] Check migration from ChartJS to "https://plotly.com/javascript/" or "https://recharts.org/" or "https://d3js.org"
* [ ] Track "https://github.com/chartjs/Chart.js/issues/11005"
* [ ] Review Portfolio growth. It Indicates negative growth, which never really happened.
* [ ] Provide more information in the Dashboard performance overview
* [ ] Migrate UI to "https://github.com/coreui/coreui"
* [ ] Add GitHub Dependabot support for Poetry: Track "https://github.com/dependabot/dependabot-core/issues/11237"
* [ ] Dividends
  * [ ] Provide more details about Dividends per year
  * [ ] Should include Dividends in the Deposit Overview?
  * [ ] Add information about the Dividend Yield
* [ ] Fees
  * [ ] Provide more details about Fees timeline
  * [ ] Provide more visual details about the fees, maybe a pie chart?
* [ ] Track delisted stocks
  * EODHD: "https://eodhd.medium.com/leveraging-delisted-stocks-for-backtesting-a-3-ema-strategy-using-python-d67221e774f5"
    * "https://eodhd.com/pricing"
  * Polygon.io: "https://polygon.io/pricing" (2 years free, rest paying)
  * Tiingo: "https://www.tiingo.com/products/end-of-day-stock-price-data"
    * "https://www.tiingo.com/documentation/end-of-day"
  * Alpaca: "https://alpaca.markets"
* [ ] DEGIRO Risk Category is a local term: "https://www.degiro.ie/helpdesk/trading-platform/what-are-risk-categories"
* [ ] Improve code quality. Check "https://pyre-check.org/docs/pysa-quickstart/"
* [ ] Enable usage of Demo DB in the application (running natively)
* [ ] Provide support to configure the settings (API Key, etc.) in the application.
  * [ ] Values should be stored in the keyring for security
* [ ] `make check-dependencies` needs some extra work
  * [ ] Review the usage of `polars` and `pandas` in the codebase and try to use only one of them
  * [ ] `toga` is only used for the `app`. Probably it should be moved as a full dependency
* [ ] IBKR
  * [ ] Obtain Deposits & Withdrawals (Based on ticket only possible with a FlexQuery up to 365 days old)
  *[ ] Show closed positions
  *[ ] Realized % Gain/Loss is not showed when merging positions
  *[ ] Stock Category
  *[ ] Stock Exchanges. Check "https://github.com/tanrbobanr/iso10383" to unify Exchange names
  *[ ] Add support for Portfolio Growth
  *[ ] Diversification: Fix sectors to be properly grouped
  *[ ] Diversification: Remove Cash and Crypto from Holdings
  *[ ] Fees: Add support for Fees
  *[ ] Transactions:
    * [ ] Add fees/taxes
    *[ ] Review provided values: Should Dividends be included in the transactions?
    *[ ] Web:
      * Performance & Reports / Transaction History: Shows transactions for the last 2 years
      *Flex Query: Allows to create custom reports.
  * [ ] Dividends: Implement Announced and Forecasted dividends
  *[ ] Deposits: Implement Deposits and Withdrawals
  *[ ] Portfolio Growth: Implement Portfolio Growth

## Logos

* [Brandfetch](https://docs.brandfetch.com/docs/getting-started) (requires API Key)
* [Alpaca](https://docs.alpaca.markets/docs/getting-started-with-alpaca-market-data) (Logos and Data) (requires API Key)
* [EOHD](https://eodhd.com/financial-apis-blog/40000-company-logos) (requires API Key)
* [nvstly](https://github.com/nvstly/icons) (misses icons)
* [NASDAQ](https://data.nasdaq.com/databases/LOGO) (requires Token)
* [Stock Analysis](https://logos.stockanalysis.com/aapl.svg) (misses some stocks)
* [Logo](https://docs.logo.dev/logo-images/ticker) (requires Token) [review]
* [Parqet](https://developers.parqet.com/blog/parqet-logo-api-guide) (misses some stocks)

## Portfolio Performance

* [PortfoliosLab](https://portfolioslab.com/tools/stock-comparison/AAPL/MSFT)
* [Stonksfolio](https://stonksfolio.com/portfolios/4qltYv/performance)
* [Quantinsti](https://blog.quantinsti.com/portfolio-analysis-performance-measurement-evaluation/)

* TWRR focuses purely on the timing of cash flows, providing an accurate measure of performance that disregards the
  amount of money involved.
* XIRR, on the other hand, considers both the timing and the size of cash flows, offering a complete picture of
  investment returns.

## Libraries

* [QuantStats](https://pypi.org/project/QuantStats/)
* [quantlib](https://quantlib-python-docs.readthedocs.io/en/latest/)
* [awesome-quant](https://github.com/wilsonfreitas/awesome-quant?tab=readme-ov-file#python)
* [PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt)
* [pyxirr](https://pypi.org/project/pyxirr/)

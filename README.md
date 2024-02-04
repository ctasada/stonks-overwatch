# Stocks Portfolio

## Start Developing

### With Docker
```shell
docker compose build
docker compose up
```

### Without Docker

Install Dependencies
```shell
poetry install
```

Run the server
```shell
poetry run src/manage.py runserver
open http://127.0.0.1:8000/degiro
```

Create Migrations
```shell
poetry run src/manage.py makemigrations degiro
```

Create Database
```shell
poetry run src/manage.py migrate
poetry run src/manage.py runscript account_import
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

## TODOs
- [ ] DeGiro Client: Replace the Singleton by a proper session instance
- [ ] DeGiro Client: Stop using Totp and request 2FA for each connection
- [ ] Portfolio: Show filter to see Open/Close/All stocks
- [ ] Improve side-bar behaviour
- [ ] Replace dicts by properly designed models
- [ ] Provide support for both Unrealized and Realized Gain/Loss
        Onger. W/V € - Gain/Loss Unrealized - unrealizedPl
        Totale W/V € - Gain/Loss Total (Realized + unrealized) - totalPl
- [ ] Would be interesting to add filters to the Account Overview page and aggregate
- [ ] Add graph with Portfolio Cumulative P&L / Cumulative Net Contributions / Portfolio NAV (https://www.investopedia.com/terms/n/nav.asp)

## Data Structure

### Account (Overview / Report)
The list of cash movements. Fields are:

Datum,Tijd,Valutadatum,Product,ISIN,Omschrijving,FX,Mutatie,,Saldo,,Order Id
Date,Time,Value Date,Product,ISIN,Description,FX,Movement (currency),Movement,Balance (currency),Balance,Order Id


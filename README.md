# Stocks Portfolio

## Start Developing

### With Docker
```shell
docker compose build
docker compose up
```

### Without Docker
```shell
python3 -m venv venv
source venv/bin/activate
# For Windows
.\venv\Scripts\activate.bat
```

Install Dependencies
```shell
pip install -r requirements.txt
```

Run the server
```shell
python src/manage.py runserver
```

## Update Dependencies
```shell
pip list --outdated
pip freeze > requirements.txt
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

## HowTos
* [Bootstrap Sidebar](https://bootstrapious.com/p/bootstrap-sidebar)
* [Mastering Multi-hued Color Scales with Chroma.js](https://www.vis4.net/blog/2013/09/mastering-multi-hued-color-scales/)

**Should we replace Django by Flask?**

## Other interesting projects
* https://github.com/leo-pfeiffer/portfolio_dashboard

## TODOs
- [ ] DeGiro Client: Replace the Singleton by a proper session instance
- [ ] DeGiro Client: Stop using Totp and request 2FA for each connection
- [ ] Portfolio: Show filter to see Open/Close/All stocks
- [ ] Improve side-bar behaviour
- [ ] Replace dicts by properly designed models
- [ ] Provide support for both Unrealized and Realized Gain/Loss
        Onger. W/V € - Gain/Loss Unrealized - unrealizedPl
        Totale W/V € - Gain/Loss Total (Realized + unrealized) - totalPl


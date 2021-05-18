# Stocks Portfolio

## Start Developing

```shell
python3 -m venv venv
source venv/bin/activate
```

For Windows
```shell
python3 -m venv venv
.\venv\Scripts\activate.bat
```

Install Dependencies
```shell
pip install -r requirements.txt
```

Update Dependencies
```shell
pip freeze > requirements.txt
```

Run the server
```shell
python manage.py runserver
```

## Documentation

* [DeGiro Connector](https://github.com/Chavithra/degiro-connector)
* [Bootstrap](https://getbootstrap.com)

## Ideas

* [Django Jazzmin](https://github.com/farridav/django-jazzmin)
* [Django Bootstrap Tutorial](https://github.com/thalesbruno/django_bootstrap)
* [Django Bootstrap-4](https://github.com/zostera/django-bootstrap4)

## HowTos
* [Bootstrap Sidebar](https://bootstrapious.com/p/bootstrap-sidebar)
* [Mastering Multi-hued Color Scales with Chroma.js](https://www.vis4.net/blog/2013/09/mastering-multi-hued-color-scales/)

**Should we replace Django by Flask?**

## TODOs
- [ ] DeGiro Client: Replace the Singleton by a proper session instance
- [ ] DeGiro Client: Stop using Totp and request 2FA for each connection
- [ ] Portfolio: Show filter to see Open/Close/All stocks
- [ ] Improve side-bar behaviour
- [ ] Replace dicts by properly designed models
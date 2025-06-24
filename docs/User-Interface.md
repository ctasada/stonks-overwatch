# Developing the User Interface

The user interface of **Stonks Overwatch** is build with the next technologies:

- [Bootstrap](https://getbootstrap.com) for the CSS framework
- [Bootstrap Table](https://bootstrap-table.com/) for the tables
- [Bootstrap Icons](https://icons.getbootstrap.com/) for the icons
- [Font Awesome](https://fontawesome.com/) for additional icons
- [Charts.js](https://www.chartjs.org/) for the charts
- [Toga](https://toga.readthedocs.io/en/stable/) for the native application

The code for the user interface is located in the `src/stonks_overwatch/templates` directory.
The templates are written in HTML and use the Jinja2 templating engine to render dynamic content.

The necessary static files (CSS, JS, images) are located in the `src/stonks_overwatch/static` directory.

## Technical details

The requested path will be resolved to a view using the `src/stonks_overwatch/urls.py` file. The view will then render
the template and return it to the client.

The templates are located in the `src/stonks_overwatch/templates` directory and are organized by feature. Each feature
has its own subdirectory with the templates related to that feature.

By default, the templates are rendered using the `base.html` template, which includes the necessary CSS and JS files.

The CSS and JS files are located in the `src/stonks_overwatch/staticfiles` directory. The Node.js files are installed
using `npminstall` (which wraps `npm` for Python) and are located in the `src/stonks_overwatch/staticfiles/node_modules`
directory.

The templates are using Bootstrap for the layout and styling, Bootstrap Table for the tables and Charts.js for the charts.

Some custom components are also used and are located either in the `src/stonks_overwatch/templates` directory or in the
`src/stonks_overwatch/staticfiles` directory.

> **Note:** It's important to note that for the application to work correctly all the static files **must** be collected
> using the `collectstatic` command. This will copy all the static files to the `src/stonks_overwatch/static` folder.

## Native Application

The native application is built using [Toga](https://toga.readthedocs.io/en/stable/)

The native application is very light and simple. A webview is used to display the web interface, which is the same as the one used in the browser.

The application provides some extra features to the user, such as:
- About dialog: Shows the version and build of the application.
- Tools:
  - Export internal database: Allows the user to export the internal database to a file. This is useful for debugging.
  - Clear cache: Allows the user to clear the caches of the application.
  - Show logs: Opens the log view.
- Help:
  - Bug report / Feedback: Redirects to a Google Form to collect feedback.
  - Visit Homepage: Will redirect to the public site.

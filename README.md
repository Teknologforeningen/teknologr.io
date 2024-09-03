# teknologr.io [![Build Status](https://travis-ci.org/Teknologforeningen/teknologr.io.svg?branch=develop)](https://travis-ci.org/Teknologforeningen/teknologr.io)  [![Coverage Status](https://coveralls.io/repos/github/Teknologforeningen/teknologr.io/badge.svg?branch=develop)](https://coveralls.io/github/Teknologforeningen/teknologr.io?branch=develop)
Membership teknologr/management system tailored for TF use

## Installation

Clone the repository, go into the root directory of the project and do the following:

1. Install prerequisites
    ```
    sudo apt install libsasl2-dev python3-dev libldap2-dev libssl-dev libpq-dev
    pip install virtualenv
    ```

1. Create a virtual environment
    ```
    virtualenv -p /usr/bin/python3 venv
    ```

1. Activate said virtual enviroment. **You need to do this for every new session.**
    ```
    source venv/bin/activate
    ```

1. Install prerequisites with pip
    ```
    pip install -r requirements.txt
    ```

1. Create a .env file
    ```
    cp teknologr/.env.example teknologr/.env
    ```
    During development you probably want to set `DEBUG=True`, and you might need to at least change the database location too to get it work out of the box. I suggest you remove the `DATABASE=...` completely to use the default database path (`teknologr/db.sqlite3`).

1. Make sure you have the correct locale available on your system. The default locale used by Teknologr.io is `sv_FI.utf8`.
    ```
    sudo locale-gen sv_FI.utf8
    sudo update-locale
    ```

1. Run migrations to update the database schema
    ```
    python teknologr/manage.py migrate
    ```

1. Create a new superuser account
    ```
    python teknologr/manage.py createsuperuser
    ```

1. You are now ready to run an instance of Teknologr.io
    ```
    python teknologr/manage.py runserver
    ```
    View the page in your browser at `http://localhost:8000`. The admin site can be found at `http://localhost:8000/admin`.


## Tests
There is a number of unittests in files named `tests_*.py`. To run all the tests:
```
python teknologr/manage.py test
```

To run only a specific test:
```
python teknologr/manage.py test members.tests_models.GroupTest
```

A certain code style is required. Run the PEP8 test to check the style:
```
python teknologr/manage.py test teknologr.tests_pep8
```

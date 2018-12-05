# vpmo

## Deployment Notes

`ng build --output-path=vpmo/dist/` should be used for building the angular frontend into the backend

Whenever the `settings.py` file is changed, the `prod_settings.py` file on the server must be changed if the change is required on deployment as well.

`sudo systemctl restart apache2` should be used to update the deployed code

`python manage.py collectstatic` must be used to update frontend code on deployment followed by the apache restart
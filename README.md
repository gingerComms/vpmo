# vpmo

## Deployment Notes

`ng build --output-path=vpmo/dist/` should be used for building the angular frontend into the backend

Whenever the `settings.py` file is changed, the `prod_settings.py` file on the server must be changed if the change is required on deployment as well.

`sudo systemctl restart apache2` should be used to update the deployed code

`python manage.py collectstatic` must be used to update frontend code on deployment followed by the apache restart


## Mongo Security Notes

The Mongo database must be run deployed with enabled authentication - through a user created in admin with the `userAdminAnyDatabase` role. After the `security.authorization` setting has been set to `"enabled"` in the Mongo settings, the user can be logged in by switching to the `admin` database after connecting through the mongo shell and using:

```db.auth("<username>", "<pass>")``` 

Which grants permissions to do everything else on the mongo database.

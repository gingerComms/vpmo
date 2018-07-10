from django.contrib.auth.models import BaseUserManager


# http://django.readthedocs.io/en/latest/topics/auth/customizing.html
class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        extra_fields.setdefault('is_superuser', False)
        if not email:
            raise ValueError('Users must have an email address')        
        
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(
            email,
            password=password,
            **extra_fields
        )
        user.save(using=self._db)
        return user


# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#abstractbaseuser
# class MyUserManager(BaseUserManager):
#     use_in_migrations = True
#
#     def _create_user(self, email, password):
#         """
#         Creates and saves a User with the given email and password.
#         """
#         if not email:
#             raise ValueError('The given email must be set')
#         email = self.normalize_email(email)
#         user = self.model(email=email)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#         user.save(using=self._db)
#     # def save(self, **kwargs):
#     #     """saving to DB disabled"""
#     #     pass
#
#     def create_user(self, email, password=None, **extra_fields):
#         # extra_fields.setdefault('is_staff', False)
#         extra_fields.setdefault('is_superuser', False)
#         extra_fields.setdefault('last_login', timezone.now())
#         return self._create_user(email, password)
#
#     def create_superuser(self, email, password, **extra_fields):
#         extra_fields.setdefault('is_superuser', True)
#         # extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('last_login', timezone.now())
#
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')
#
#         return self._create_user(email, password, **extra_fields)
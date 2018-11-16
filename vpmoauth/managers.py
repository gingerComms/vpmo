from django.contrib.auth.models import BaseUserManager


# http://django.readthedocs.io/en/latest/topics/auth/customizing.html
class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
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
        # acquire token or required permissions to be able to create team

        user.create_user_team()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
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
        # acquire token to be able to create team
        user.create_user_team()
        return user

    def get_by_natural_key(self, email):
        return self.get(email=email)


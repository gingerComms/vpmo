from django.test import TestCase
from .models import MyUser
import test_addons

# Create your tests here.


class ModelTestCase(test_addons.MongoTestCase):
    # A MongoTestCase needs this argument to use the test database
    allow_database_queries = True

    # creating a song in setup to run multiple tests with one object
    def setUp(self):
        self.old_count = MyUser.objects.count()
        self.object = MyUser.objects.create(email="ali@test.com", first_name="Ali", last_name="Rad")

    # deletion after tests are complete
    def tearDown(self):
        self.object.delete()

    # basic count test
    def test_model_can_create(self):
        new_count = MyUser.objects.count()
        self.assertNotEqual(self.old_count, new_count)


    """ The following two tests are included to ensure django ids and pks are not interfered in the djongo compiling. See full doc for more on my experience with this """
    def test_model_has_id(self):
        self.assertIsNotNone(self.object.id)

    def test_model_has_pk(self):
        self.assertIsNotNone(self.object.pk)

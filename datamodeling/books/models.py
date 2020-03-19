from django.db import models


# Create your models here.
class Book(models.Model):
    isbn_13 = models.CharField(max_length=13, blank=True, null=True)
    isbn_10 = models.CharField(max_length=10, blank=True, null=True)
    title = models.CharField(max_length=100, unique=True)
    price = models.IntegerField(blank=True, null=True)
    pub_date = models.DateField()
    page = models.IntegerField(blank=True, null=True)
    headline = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    publisher = models.ForeignKey('Publisher', on_delete=models.CASCADE, related_name='books')
    rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.title


class Publisher(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    books = models.ManyToManyField('Book', related_name='authors')

    def __str__(self):
        return self.name

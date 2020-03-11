from django.db import models


# Create your models here.
class Book(models.Model):
    isbn = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    price = models.IntegerField()
    pub_date = models.DateField()
    publisher = models.ForeignKey('Publisher', on_delete=models.CASCADE, related_name='books')

    def __str__(self):
        return self.title


class Publisher(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    books = models.ManyToManyField('Book', related_name='authors')

    def __str__(self):
        return self.name

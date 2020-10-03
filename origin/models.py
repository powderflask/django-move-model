from django.db import models


class ModelToMove(models.Model):
    title = models.CharField('Title', max_length=100)
    data = models.IntegerField('A piece of data', default=42)
    new_field = models.CharField('Something new', max_length=100, blank=True, default='')

    def __str__(self):
        return '{title} ({data})'.format(title=self.title, data=self.data)

from django.db import models

class Example(models.Model):
    related_object = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='examples')
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Example by {self.related_object} on {self.date_created}"

    class Meta:
        verbose_name = 'Example'
        verbose_name_plural = 'Examples'
        ordering = ['-date_created']

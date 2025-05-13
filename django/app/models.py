from django.db import models

class Image(models.Model):
    s3_file_path = models.CharField(max_length=1024)
    description = models.TextField()

    def __str__(self):
        return self.s3_file_path

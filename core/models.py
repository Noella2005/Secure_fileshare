import os
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UploadedFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_files')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # We use a ManyToManyField for flexible sharing permissions
    shared_with = models.ManyToManyField(User, related_name='shared_files', blank=True)

    def __str__(self):
        return os.path.basename(self.file.name)

    def get_filename(self):
        return os.path.basename(self.file.name)
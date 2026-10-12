from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=170, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "organizations"

    def __str__(self):
        return self.name


class User(AbstractUser):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    @property
    def display_name(self):
        return self.get_full_name().strip() or self.username

    def __str__(self):
        return self.display_name

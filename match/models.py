from django.db import models
from users.models import User

class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_user2')
    match_score = models.IntegerField()
    status = models.CharField(max_length=20)

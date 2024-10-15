from django.db import models
from django.contrib.auth.models import User
from accounts.models import User,Child

class ChildcareJournal(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    published_on = models.DateField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_public = models.BooleanField(default=False)
    impression_count = models.PositiveIntegerField(default=0) 
    image_url = models.FileField(upload_to='uploads/', null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "childcare_journals"

class Hashtag(models.Model):
    hashtag_word = models.CharField(max_length=255, unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "hashtags"

class ChildcareJournalHashtag(models.Model):
    childcare_journal = models.ForeignKey(ChildcareJournal, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "childcare_journals_hashtags"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    childcare_journal = models.ForeignKey(ChildcareJournal, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "favorites"

class ChildcareJournalAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    childcare_journal = models.ForeignKey(ChildcareJournal, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField() 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "childcare_journals_access_logs"

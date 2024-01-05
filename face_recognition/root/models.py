from django.db import models

class Student(models.Model):
    sid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    class_number = models.IntegerField(db_column='class')
    total_present = models.IntegerField()
    date = models.DateField()

    class Meta:
        db_table = 'student_table'

    def __str__(self):
        return self.name

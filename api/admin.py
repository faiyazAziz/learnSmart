from django.contrib import admin
from .models import Book, Topic, Question, Quiz, QuizSession, UserAnswer

# Register your models here.
admin.site.register(Book)
admin.site.register(Topic)
admin.site.register(Question)
admin.site.register(Quiz)
admin.site.register(QuizSession)
admin.site.register(UserAnswer)


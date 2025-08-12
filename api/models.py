# api/models.py

from django.db import models
from django.contrib.auth.models import User

# Book and Topic models remain the same
class Book(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    full_text = models.TextField(blank=True, null=True)
    processing_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[('pending', 'Pending'), ('processing', 'Processing'), ('complete', 'Complete')]
    )
    def __str__(self):
        return self.title

class Topic(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.title} (Book: {self.book.title})"


# --- MODEL CHANGES ARE BELOW ---

class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    # REMOVED: The ManyToManyField is no longer needed here.
    # The relationship is now handled by the ForeignKey in the Question model.

    def __str__(self):
        return f"Quiz for {self.user.username} on Book: {self.book.title}"

class Question(models.Model):
    # UPDATED: A Question now belongs to exactly one Quiz.
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    # We can still store the source topic for reference, but it's not the main link.
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, related_name='generated_questions')
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=10)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.question_text[:50]

# These models are now correct because the ambiguity is gone.
class QuizSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_sessions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sessions')
    score = models.FloatField(null=True, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attempt by {self.user.username} on Quiz {self.quiz.id}"

class UserAnswer(models.Model):
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=10)
    is_correct = models.BooleanField()

    def __str__(self):
        return f"Answer for Q:{self.question.id} in Session:{self.quiz_session.id}"

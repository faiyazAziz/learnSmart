# api/serializers.py

from rest_framework import serializers
from .models import (
    Book, Topic, Question, Quiz, QuizSession, UserAnswer
)

# --- Serializers for Book/Topic (already exist) ---
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'uploaded_at', 'processing_status']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'book', 'title']

class BookUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    pdf_file = serializers.FileField(write_only=True)


# --- Serializers for Quiz Creation (already exist) ---
class QuizCreateSerializer(serializers.Serializer):
    topic_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    book_id = serializers.IntegerField()


# --- Serializers for Taking the Quiz and Getting Results ---

# 1. For FETCHING the quiz (hides correct answers)
class QuestionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'options'] # Note: correct_answer is excluded

class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionDetailSerializer(many=True, read_only=True)
    class Meta:
        model = Quiz
        fields = ['id', 'user', 'book', 'created_at', 'questions']

# Add this new serializer to display the full quiz
class QuizSerializer(serializers.ModelSerializer):
    # Nest the QuestionSerializer to show all questions for the quiz
    questions = QuestionDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'user', 'book', 'created_at', 'questions']
        
        
# 2. For SUBMITTING answers
class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.CharField(max_length=10)

class QuizSubmitSerializer(serializers.Serializer):
    answers = AnswerSubmitSerializer(many=True, allow_empty=False)


# 3. For DISPLAYING the final results
class QuestionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        # Here we reveal all details for feedback
        fields = ['id', 'question_text', 'options', 'correct_answer', 'explanation']

class UserAnswerResultSerializer(serializers.ModelSerializer):
    question = QuestionResultSerializer(read_only=True)
    class Meta:
        model = UserAnswer
        fields = ['question', 'selected_answer', 'is_correct']

class QuizSessionResultSerializer(serializers.ModelSerializer):
    user_answers = UserAnswerResultSerializer(many=True, read_only=True)
    class Meta:
        model = QuizSession
        fields = ['id', 'user', 'quiz', 'score', 'completed_at', 'user_answers']






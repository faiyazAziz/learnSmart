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
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            'id',
            'book',
            'title',
            'accuracy',
            'accuracy_last_updated',
            'correct_answers',
            'wrong_answers',
            'total_questions',
        ]

    def get_total_questions(self, obj):
        return obj.generated_questions.count()

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


        
        
class QuizListSerializer(serializers.ModelSerializer):
    """
    A serializer for listing quizzes, now including the total number of questions
    and a list of topics covered.
    """
    book_title = serializers.CharField(source='book.title', read_only=True)
    # NEW: Custom fields to compute additional data
    total_questions = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        # Add the new fields to the list
        fields = ['id', 'book', 'book_title', 'created_at', 'total_questions', 'topics']

    def get_total_questions(self, obj):
        """
        Calculates the total number of questions for the quiz instance.
        'obj' here is the Quiz instance.
        """
        return obj.questions.count()

    def get_topics(self, obj):
        """
        Gathers a list of unique topic titles covered in the quiz.
        """
        # We query the topics related to the questions in this specific quiz,
        # get their titles, and return only the unique ones.
        return list(
            obj.questions.select_related('topic')
                         .values_list('topic__title', flat=True)
                         .distinct()
        )
        
class QuizSessionResultSerializer(serializers.ModelSerializer):
    user_answers = UserAnswerResultSerializer(many=True, read_only=True)
    quiz = QuizListSerializer()
    class Meta:
        model = QuizSession
        fields = ['id', 'user', 'quiz', 'score', 'completed_at', 'user_answers']


class QuizSessionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing past attempts (sessions) for a specific quiz.
    """
    class Meta:
        model = QuizSession
        fields = ['id', 'score', 'completed_at']

class IncorrectQuestionSerializer(serializers.ModelSerializer):
    """
    A serializer to display the details of questions the user answered incorrectly.
    It shows the user's wrong answer and the correct answer for review.
    """
    # We nest the QuestionResultSerializer to show all details of the question
    question = QuestionResultSerializer(read_only=True)

    class Meta:
        model = UserAnswer
        # We only need to show the question details and the user's wrong answer
        fields = ['question', 'selected_answer']





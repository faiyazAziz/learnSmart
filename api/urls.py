from django.urls import path
from .views import (BookUploadView, TopicListView, QuizCreateView, QuizDetailView, 
                    QuizSubmitView, BookListView, QuizListView, QuizSessionListView,
                    QuizSessionDetailView, IncorrectQuestionsListView)

urlpatterns = [
    # Endpoint for Book related
    path('books/upload/', BookUploadView.as_view(), name='book-upload'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:book_pk>/topics/', TopicListView.as_view(), name='book-topics'),
    
    # Quiz URLs
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/create/', QuizCreateView.as_view(), name='quiz-create'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:quiz_pk>/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
    path('quizzes/<int:quiz_pk>/sessions/', QuizSessionListView.as_view(), name='quiz-sessions'),
    
    path('quiz-sessions/<int:pk>/', QuizSessionDetailView.as_view(), name='quiz-session-detail'),
    
    path('insights/incorrect-questions/', IncorrectQuestionsListView.as_view(), name='incorrect-questions-list'),
]


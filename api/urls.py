from django.urls import path
from .views import BookUploadView, TopicListView, QuizCreateView, QuizDetailView, QuizSubmitView

urlpatterns = [
    # Endpoint for uploading a book
    path('books/upload/', BookUploadView.as_view(), name='book-upload'),
    path('books/<int:book_pk>/topics/', TopicListView.as_view(), name='book-topics'),
    path('quizzes/create/', QuizCreateView.as_view(), name='quiz-create'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:quiz_pk>/submit/', QuizSubmitView.as_view(), name='quiz-submit'),
]
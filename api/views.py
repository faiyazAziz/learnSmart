from rest_framework import generics, status, parsers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Book, Topic, Quiz, Question,QuizSession, UserAnswer
from .serializers import BookSerializer, BookUploadSerializer, TopicSerializer, QuizSerializer, QuizCreateSerializer, QuizDetailSerializer,QuizSubmitSerializer,QuizSessionResultSerializer
from .services import extract_text_from_pdf, get_topics_from_text,get_questions_for_topic

class BookUploadView(generics.CreateAPIView):
    """
    An API view to handle PDF book uploads and initiate processing.
    """
    serializer_class = BookUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the validated data
        title = serializer.validated_data['title']
        pdf_file = serializer.validated_data['pdf_file']

        # --- Start Processing ---
        try:
            # 1. Extract text from the in-memory PDF file
            print("Starting text extraction...")
            full_text = extract_text_from_pdf(pdf_file)
            if not full_text:
                return Response({"error": "Could not extract text from the PDF."}, status=status.HTTP_400_BAD_REQUEST)
            print("Text extraction complete.")

            # 2. Get topics from the extracted text
            print("Starting topic generation...")
            topics_list = get_topics_from_text(full_text)
            if not topics_list:
                return Response({"error": "AI could not generate topics from the document."}, status=status.HTTP_400_BAD_REQUEST)
            print("Topic generation complete.")

            # 3. Save the Book and Topic objects to the database
            book = Book.objects.create(
                user=self.request.user,
                title=title,
                full_text=full_text,
                processing_status='complete'
            )

            for topic_title in topics_list:
                Topic.objects.create(book=book, title=topic_title)
            print("Book and topics saved successfully.")

            # 4. Return the data of the newly created book
            final_serializer = BookSerializer(book)
            return Response(final_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({"error": "An unexpected error occurred during processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopicListView(generics.ListAPIView):
    """
    An API view to list all topics for a specific book.
    """
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the topics
        for the book as determined by the book_id portion of the URL.
        """
        # Get the book_id from the URL kwargs
        book_id = self.kwargs['book_pk']
        
        # Get the specific book, ensuring it belongs to the logged-in user
        book = get_object_or_404(Book, id=book_id, user=self.request.user)
        
        # Return the topics related to that book
        return Topic.objects.filter(book=book)
    
class QuizCreateView(generics.CreateAPIView):
    """
    An API view to create a quiz by generating questions for a list of topics.
    """
    serializer_class = QuizCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic_ids = serializer.validated_data['topic_ids']
        book_id = serializer.validated_data['book_id']

        # 1. Verify that the book and topics belong to the user
        book = get_object_or_404(Book, id=book_id, user=request.user)
        topics = Topic.objects.filter(id__in=topic_ids, book=book)

        if len(topic_ids) != topics.count():
            return Response({"error": "One or more topics are invalid or do not belong to the specified book."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Create the main Quiz instance
        quiz = Quiz.objects.create(user=request.user, book=book)
        # print(quiz.id)

        # 3. Generate and save questions for each topic
        try:
            for topic in topics:
                print(f"Generating questions for topic: {topic.title}")
                # Use the book's stored full_text for context
                questions_data = get_questions_for_topic(topic.title, book.full_text)

                if not questions_data:
                    print(f"Warning: Could not generate questions for topic ID {topic.id}.")
                    continue # Move to the next topic

                for q_data in questions_data:
                    question = Question.objects.create(
                        topic=topic,
                        quiz=quiz,
                        question_text=q_data.get('question_text'),
                        options=q_data.get('options'),
                        correct_answer=q_data.get('correct_answer'),
                        explanation=q_data.get('explanation')
                    )
                    # Add the newly created question to our quiz
                    quiz.questions.add(question)

            if not quiz.questions.exists():
                # If after all topics, no questions were generated, it's an error.
                quiz.delete() # Clean up the empty quiz
                return Response({"error": "Failed to generate any questions for the selected topics."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 4. Serialize and return the complete quiz
            final_serializer = QuizSerializer(quiz)
            return Response(final_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Clean up the created quiz if a critical error occurs
            quiz.delete()
            print(f"An unexpected error occurred during quiz creation: {e}")
            return Response({"error": "An unexpected error occurred during quiz generation."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        
# To fetch a specific quiz for the user to take
class QuizDetailView(generics.RetrieveAPIView):
    """
    Retrieves a single quiz with its questions, ready for the user to answer.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Ensure users can only access their own quizzes."""
        return Quiz.objects.filter(user=self.request.user)


# UPDATED VIEW: To handle the submission of answers
class QuizSubmitView(generics.GenericAPIView):
    """
    Handles the submission of a completed quiz, calculates the score,
    and returns a detailed breakdown of the results.
    """
    serializer_class = QuizSubmitSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_pk, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=quiz_pk, user=request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data['answers']

        session = QuizSession.objects.create(user=request.user, quiz=quiz)
        correct_answers_count = 0
        
        # Create a dictionary of submitted answers for quick lookup
        answers_dict = {ans['question_id']: ans['selected_answer'] for ans in submitted_answers}
        
        # Get all questions for the quiz at once
        quiz_questions = quiz.questions.all()

        for question in quiz_questions:
            selected_answer = answers_dict.get(question.id)
            is_correct = False
            if selected_answer:
                is_correct = (question.correct_answer.lower() == selected_answer.lower())
                if is_correct:
                    correct_answers_count += 1
            
            UserAnswer.objects.create(
                quiz_session=session,
                question=question,
                selected_answer=selected_answer or "", # Store empty string if not answered
                is_correct=is_correct
            )

        if quiz_questions.count() > 0:
            score = (correct_answers_count / quiz_questions.count()) * 100
            session.score = round(score, 2)
            session.save()

        result_serializer = QuizSessionResultSerializer(session)
        return Response(result_serializer.data, status=status.HTTP_200_OK)
     
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
          
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
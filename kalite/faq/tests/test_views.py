from __future__ import absolute_import

import datetime
import django.test
import mock
import os
from django.conf import settings
from faq.models import Topic, Question

class FAQViewTests(django.test.TestCase):
    urls = 'faq.urls'
    fixtures = ['faq_test_data.json']

    def setUp(self):
        # Make some test templates available.
        self._oldtd = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__), 'templates')]

    def tearDown(self):
        settings.TEMPLATE_DIRS = self._oldtd
    
    def test_submit_faq_get(self):
        response = self.client.get('/submit/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq/submit_question.html")

#    @mock.patch('django.contrib.messages')
    def test_submit_faq_post(self, mock_messages):
        data = {
            'topic': '1',
            'text': 'What is your favorite color?',
            'answer': 'Blue. I mean red. I mean *AAAAHHHHH....*',
        }
        response = self.client.post('/submit/', data)
        mock_messages.sucess.assert_called()
        self.assertRedirects(response, "/submit/thanks/")
        self.assert_(
            Question.objects.filter(text=data['text']).exists(),
            "Expected question object wasn't created."
        )
        
    def test_submit_thanks(self):
        response = self.client.get('/submit/thanks/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq/submit_thanks.html")
    
    def test_faq_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq/topic_list.html")
        self.assertQuerysetEqual(
            response.context["topics"],
            ["<Topic: Silly questions>", "<Topic: Serious questions>"]
        )
        self.assertEqual(
            response.context['last_updated'],
            Question.objects.order_by('-updated_on')[0].updated_on
        )
        
    def test_topic_detail(self):
        response = self.client.get('/silly-questions/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq/topic_detail.html")
        self.assertEqual(
            response.context['topic'],
            Topic.objects.get(slug="silly-questions")
        )
        self.assertEqual(
            response.context['last_updated'],
            Topic.objects.get(slug='silly-questions').questions.order_by('-updated_on')[0].updated_on
        )
        self.assertQuerysetEqual(
            response.context["questions"],
            ["<Question: What is your favorite color?>", 
             "<Question: What is your quest?>"]
        )
    
    def test_question_detail(self):
        response = self.client.get('/silly-questions/your-quest/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq/question_detail.html")
        self.assertEqual(
            response.context["question"],
            Question.objects.get(slug="your-quest")
        )

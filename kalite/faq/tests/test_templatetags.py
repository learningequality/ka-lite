from __future__ import absolute_import

import django.test
from django import template
from django.utils import unittest
from ..templatetags import faqtags
from ..models import Topic

class FAQTagsSyntaxTests(unittest.TestCase):
    """
    Tests for the syntax/compliation functions.
    
    These are broken out here so that they don't have to be
    django.test.TestCases, which are slower.
    """
    
    def compile(self, tagfunc, token_contents):
        """
        Mock out a call to a template compliation function.
        
        Assumes the tag doesn't use the parser, so this won't work for block tags.
        """
        t = template.Token(template.TOKEN_BLOCK, token_contents)
        return tagfunc(None, t)
    
    def test_faqs_for_topic_compile(self):
        t = self.compile(faqtags.faqs_for_topic, "faqs_for_topic 15 'some-slug' as faqs")
        self.assertEqual(t.num.var, "15")
        self.assertEqual(t.topic.var, "'some-slug'")
        self.assertEqual(t.varname, "faqs")
        
    def test_faqs_for_topic_too_few_arguments(self):
        self.assertRaises(template.TemplateSyntaxError,
                          self.compile, 
                          faqtags.faqs_for_topic, 
                          "faqs_for_topic 15 'some-slug' as")
        
    def test_faqs_for_topic_too_many_arguments(self):
        self.assertRaises(template.TemplateSyntaxError,
                          self.compile, 
                          faqtags.faqs_for_topic, 
                          "faqs_for_topic 15 'some-slug' as varname foobar")
                          
    def test_faqs_for_topic_bad_as(self):
        self.assertRaises(template.TemplateSyntaxError,
                          self.compile, 
                          faqtags.faqs_for_topic, 
                          "faqs_for_topic 15 'some-slug' blahblah varname")
    
    def test_faq_list_compile(self):
        t = self.compile(faqtags.faq_list, "faq_list 15 as faqs")
        self.assertEqual(t.num.var, "15")
        self.assertEqual(t.varname, "faqs")
        
    def test_faq_list_too_few_arguments(self):
        self.assertRaises(template.TemplateSyntaxError,
                          self.compile, 
                          faqtags.faq_list, 
                          "faq_list 15")
        
    def test_faq_list_too_many_arguments(self):
        self.assertRaises(template.TemplateSyntaxError,
                          self.compile, 
                          faqtags.faq_list, 
                          "faq_list 15 as varname foobar")
                          
    def test_faq_list_bad_as(self):
        self.assertRaises(template.TemplateSyntaxError,
                          self.compile, 
                          faqtags.faq_list, 
                          "faq_list 15 blahblah varname")

class FAQTagsNodeTests(django.test.TestCase):
    """
    Tests for the node classes themselves, and hence the rendering functions.
    """
    fixtures = ['faq_test_data.json']
    
    def test_faqs_for_topic_node(self):
        context = template.Context()
        node = faqtags.FaqListNode(num='5', topic='"silly-questions"', varname="faqs")
        content = node.render(context)
        self.assertEqual(content, "")
        self.assertQuerysetEqual(context['faqs'], 
            ['<Question: What is your favorite color?>',
             '<Question: What is your quest?>'])
             
    def test_faqs_for_topic_node_variable_arguments(self):
        """
        Test faqs_for_topic with a variable arguments.
        """
        context = template.Context({'topic': Topic.objects.get(pk=1),
                                    'number': 1})
        node = faqtags.FaqListNode(num='number', topic='topic', varname="faqs")
        content = node.render(context)
        self.assertEqual(content, "")
        self.assertQuerysetEqual(context['faqs'], ["<Question: What is your favorite color?>"])
    
    def test_faqs_for_topic_node_invalid_variables(self):
        context = template.Context()
        node = faqtags.FaqListNode(num='number', topic='topic', varname="faqs")
        content = node.render(context)
        self.assertEqual(content, "")
        self.assert_("faqs" not in context,
                     "faqs variable shouldn't have been added to the context.")
    
    def test_faq_list_node(self):
        context = template.Context()
        node = faqtags.FaqListNode(num='5', varname="faqs")
        content = node.render(context)
        self.assertEqual(content, "")
        self.assertQuerysetEqual(context['faqs'], 
            ['<Question: What is your favorite color?>',
             '<Question: What is your quest?>',
             '<Question: What is Django-FAQ?>'])
             
    def test_faq_list_node_variable_arguments(self):
        """
        Test faqs_for_topic with a variable arguments.
        """
        context = template.Context({'topic': Topic.objects.get(pk=1),
                                    'number': 1})
        node = faqtags.FaqListNode(num='number', varname="faqs")
        content = node.render(context)
        self.assertEqual(content, "")
        self.assertQuerysetEqual(context['faqs'], ["<Question: What is your favorite color?>"])
    
    def test_faq_list_node_invalid_variables(self):
        context = template.Context()
        node = faqtags.FaqListNode(num='number', varname="faqs")
        content = node.render(context)
        self.assertEqual(content, "")
        self.assert_("faqs" not in context,
                     "faqs variable shouldn't have been added to the context.")
    

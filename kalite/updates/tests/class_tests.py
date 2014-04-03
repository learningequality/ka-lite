"""
Testing of the updates functions
"""
import datetime

from django.utils import unittest

from ..models import UpdateProgressLog
from fle_utils.general import datediff


class TestSingleStageUpdate(unittest.TestCase):
    """
    """

    def test_create(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=1)
        progress_log.save()
        self.assertEqual(progress_log.total_stages, 1, "one stage")
        self.assertEqual(progress_log.end_time, None, "end_time not set")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_update_stage(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=1)
        progress_log.save()

        # Complete the process
        progress_log.update_stage("test_stage", 0.5)
        self.assertEqual(progress_log.stage_percent, 0.5, "stage_percent set properly")
        self.assertEqual(progress_log.process_percent, 0.5, "process_percent set properly")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_cancel_current_stage(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=1)
        progress_log.save()
        progress_log.update_stage("test_stage", 0.5)

        # Complete the process
        progress_log.cancel_current_stage()
        self.assertEqual(progress_log.stage_percent, 0., "stage_percent is 0")
        self.assertEqual(progress_log.process_percent, 0., "process_percent is 0")
        self.assertEqual(progress_log.total_stages, 1, "Should still have one stage after cancel.")
        self.assertEqual(progress_log.stage_name, None, "stage name is None")
        self.assertEqual(progress_log.completed, False, "completed is False")
        self.assertEqual(progress_log.end_time, None, "end_time is not set")


    def test_update_total_stages(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=1)
        progress_log.save()
        progress_log.update_stage("test_stage", 0.5)

        # Complete the process
        progress_log.update_total_stages(10)
        self.assertEqual(progress_log.total_stages, 10, "no stages")
        self.assertEqual(progress_log.stage_percent, 0.5, "stage_percent is 0.05")
        self.assertEqual(progress_log.process_percent, 0.05, "process_percent is 0.05")
        self.assertEqual(progress_log.stage_name, "test_stage", "stage name still set")
        self.assertEqual(progress_log.completed, False, "completed is False")
        self.assertEqual(progress_log.end_time, None, "end_time is not set")


    def test_cancel_progress(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=1)
        progress_log.save()

        # Complete the process
        progress_log.cancel_progress()
        self.assertTrue(abs(datediff(progress_log.end_time, datetime.datetime.now())) < 10, "end time is within 10 seconds")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_completion(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=1)
        progress_log.save()

        # Complete the process
        progress_log.mark_as_completed()
        self.assertTrue(abs(datediff(progress_log.end_time, datetime.datetime.now())) < 10, "end time is within 10 seconds")
        self.assertEqual(progress_log.stage_percent, 1., "stage_percent==1")
        self.assertEqual(progress_log.process_percent, 1., "proces_percent==1")
        self.assertEqual(progress_log.completed, True, "completed is False")


class TestMultiStageUpdate(unittest.TestCase):
    """
    """

    def test_create(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()
        self.assertEqual(progress_log.total_stages, 10, "10 stages stage")
        self.assertEqual(progress_log.end_time, None, "end_time not set")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_update_stage(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()

        # Complete the process
        progress_log.update_stage("test_stage", 0.5)
        self.assertEqual(progress_log.stage_percent, 0.5, "stage_percent set properly")
        self.assertEqual(progress_log.process_percent, 0.05, "process_percent set properly")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_dual_update_stage(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()

        # Complete the process
        progress_log.update_stage("test_stage", 0.25)
        progress_log.update_stage("test_stage2", 0.5)  # completes stage 1
        self.assertEqual(progress_log.stage_percent, 0.5, "stage_percent set properly")
        self.assertTrue(abs(progress_log.process_percent - 0.15) < 1E10, "process_percent is 0.15")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_cancel_current_stage(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()
        progress_log.update_stage("test_stage", 0.25)
        progress_log.update_stage("test_stage2", 0.5)  # completes stage 1

        # Complete the process
        progress_log.cancel_current_stage()
        self.assertEqual(progress_log.stage_percent, 0., "stage_percent is 0")
        self.assertTrue(abs(progress_log.process_percent - 0.1) < 1E10, "process_percent is 0.1")
        self.assertEqual(progress_log.total_stages, 10, "Should still have 10 stages after cancel.")
        self.assertEqual(progress_log.stage_name, None, "stage name is None")
        self.assertEqual(progress_log.completed, False, "completed is False")
        self.assertEqual(progress_log.end_time, None, "end_time is not set")


    def test_update_total_stages(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()
        progress_log.update_stage("test_stage", 0.5)

        # Complete the process
        progress_log.update_total_stages(20)
        self.assertEqual(progress_log.total_stages, 20, "Should have 20 stages after updating total stages.")
        self.assertEqual(progress_log.stage_percent, 0.5, "stage_percent is 0.025")
        self.assertTrue(abs(progress_log.process_percent - 0.025) < 1E10, "process_percent is 0.25")
        self.assertEqual(progress_log.stage_name, "test_stage", "stage name still set")
        self.assertEqual(progress_log.completed, False, "completed is False")
        self.assertEqual(progress_log.end_time, None, "end_time is not set")


    def test_update_total_stages_in_progress(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()
        progress_log.update_stage("test_stage", 0.25)
        progress_log.update_stage("test_stage2", 0.5)

        # Complete the process
        progress_log.update_total_stages(20)
        self.assertEqual(progress_log.total_stages, 20, "Should have 20 stages after updating total stages.")
        self.assertEqual(progress_log.stage_percent, 0.5, "stage_percent is 0.05")
        self.assertTrue(abs(progress_log.process_percent - 0.075) < 1E10, "process_percent is 0.075")
        self.assertEqual(progress_log.stage_name, "test_stage2", "stage name still set")
        self.assertEqual(progress_log.completed, False, "completed is False")
        self.assertEqual(progress_log.end_time, None, "end_time is not set")


    def test_cancel_progress(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()

        # Complete the process
        progress_log.cancel_progress()
        self.assertTrue(abs(datediff(progress_log.end_time, datetime.datetime.now())) < 10, "end time is within 10 seconds")
        self.assertEqual(progress_log.completed, False, "completed is False")


    def test_completion(self):

        # Create the object
        progress_log = UpdateProgressLog(process_name="test_process", total_stages=10)
        progress_log.save()

        # Complete the process
        progress_log.mark_as_completed()
        self.assertTrue(abs(datediff(progress_log.end_time, datetime.datetime.now())) < 10, "end time is within 10 seconds")
        self.assertEqual(progress_log.stage_percent, 1., "stage_percent==1")
        self.assertEqual(progress_log.process_percent, 1., "proces_percent==1")
        self.assertEqual(progress_log.completed, True, "completed is False")


#class TestUpdatesDynamicCommand(unittest.TestCase):

from random import randint, sample
from datetime import datetime, timedelta

from django.test import TestCase
from django.db import IntegrityError

from core.models import Sample, Membership
from core.test.utils import setup_basic_test_data


class DataTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase.
        cls.test_data = setup_basic_test_data()

    def test_insert_valid_samples(self):
        stop_time = datetime.now()
        start_timestamp = round((stop_time - timedelta(days=1)).timestamp())
        stop_timestamp = round(stop_time.timestamp())
        step = timedelta(minutes=9).seconds
        times = range(start_timestamp, stop_timestamp, step)
        samples = [
            Sample.objects.create(
                node=self.test_data["node"],
                timestamp_s=ts,
                co2_ppm=400 + randint(0, 1000),
                measurement_status=Sample.MEASUREMENT,
            )
            for ts in times
        ]
        self.assertEqual(Sample.objects.all().count(), len(samples))

    def test_non_unique_samples(self):
        """For a given node, the sample timestamp must be unique."""

        ts = round(datetime.now().timestamp())
        Sample.objects.create(
            node=self.test_data["node"],
            timestamp_s=ts,
            co2_ppm=400 + randint(0, 1000),
            measurement_status=Sample.MEASUREMENT,
        )
        with self.assertRaises(IntegrityError):
            Sample.objects.create(
                node=self.test_data["node"],
                timestamp_s=ts,
                co2_ppm=400 + randint(0, 1000),
                measurement_status=Sample.MEASUREMENT,
            )

    def test_ordering(self):
        times = sample(range(1604259676), 10)
        for ts in times:
            Sample.objects.create(
                node=self.test_data["node"],
                timestamp_s=ts,
                co2_ppm=400 + randint(0, 1000),
                measurement_status=Sample.MEASUREMENT,
            )
        # Load from DB and verify ordering.
        loaded_samples = Sample.objects.all()
        loaded_timestamps = [sample.timestamp_s for sample in loaded_samples]
        cmp = 0
        for ts in loaded_timestamps:
            self.assertTrue(ts >= cmp)
            cmp = ts


class InventoryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase.
        cls.test_data = setup_basic_test_data()

    def test_unique_membership(self):
        """A user can have a single membership in a given organization only."""
        org = self.test_data["organization"]
        user = self.test_data["user"]
        with self.assertRaises(IntegrityError):
            Membership.objects.create(
                role=Membership.ASSISTANT, user=user, organization=org
            )
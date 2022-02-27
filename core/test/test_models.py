from datetime import datetime, timedelta
from random import randint, sample

from django.db import IntegrityError
from django.core.validators import ValidationError
from django.test import TestCase

from core.models import Sample, Membership, Address, Site, Room, RoomNodeInstallation
from core.test.utils import setup_basic_test_data


class DataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase.
        cls.test_data = setup_basic_test_data()

    def test_insert_valid_samples(self):
        stop_time = datetime.now()
        start_timestamp_s = round((stop_time - timedelta(days=1)).timestamp())
        stop_timestamp_s = round(stop_time.timestamp())
        step = timedelta(minutes=9).seconds
        times = range(start_timestamp_s, stop_timestamp_s, step)
        samples = [
            Sample.objects.create(
                node=self.test_data["node1"],
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
            node=self.test_data["node1"],
            timestamp_s=ts,
            co2_ppm=400 + randint(0, 1000),
            measurement_status=Sample.MEASUREMENT,
        )
        with self.assertRaises(IntegrityError):
            Sample.objects.create(
                node=self.test_data["node1"],
                timestamp_s=ts,
                co2_ppm=400 + randint(0, 1000),
                measurement_status=Sample.MEASUREMENT,
            )

    def test_ordering(self):
        times = sample(range(1604259676), 10)
        for ts in times:
            Sample.objects.create(
                node=self.test_data["node1"],
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


class InventoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase.
        cls.test_data = setup_basic_test_data()

    def test_unique_membership(self):
        """A user can have a single membership in a given organization only."""
        org = self.test_data["organization1"]
        user = self.test_data["user1"]
        with self.assertRaises(IntegrityError):
            Membership.objects.create(
                role=Membership.INSPECTOR, user=user, organization=org
            )

    def test_unique_site(self):
        """Within an organization, sites must have unique names."""
        adr = Address.objects.create(
            street1="Teststraße 1", zip="12345", city="Testdorf"
        )
        # One site with a given name and operator can be created.
        Site.objects.create(
            name="Test-Site",
            description="Nur zum Test",
            address=adr,
            operator=self.test_data["organization1"],
        )
        # A second site with the same name and operater must not exist.
        with self.assertRaises(IntegrityError):
            Site.objects.create(
                name="Test-Site",
                description="Auch zum Test",
                address=adr,
                operator=self.test_data["organization1"],
            )

    def test_unique_room(self):
        """Within a site, rooms must have unique names."""
        adr = Address.objects.create(
            street1="Teststraße 1", zip="12345", city="Testdorf"
        )
        site = Site.objects.create(
            name="Test-Site",
            description="Nur zum Test",
            address=adr,
            operator=self.test_data["organization1"],
        )
        # One room with a given name and site can be created.
        Room.objects.create(
            name="Testraum",
            description="Nur für Testzwecke",
            size_sqm=12.5,
            height_m=3.1,
            max_occupancy=2,
            site=site,
        )
        # Another room with the same name and site cannot be created.
        with self.assertRaises(IntegrityError):
            Room.objects.create(
                name="Testraum",
                description="Auch ein Testzwecke",
                size_sqm=125,
                height_m=31,
                max_occupancy=20,
                site=site,
            )

    def test_installation(self):
        """Node and room referenced in a NodeInstallation must pertain to the same owner."""
        installation = RoomNodeInstallation.objects.create(
            description="A fine installation",
            from_timestamp_s=1577836800,
            to_timestamp_s=2147483647,
            is_public=True,
            node=self.test_data["node2"],
            room=self.test_data["room2"],
        )
        self.assertEqual(installation.from_timestamp_s, 1577836800)
        self.assertEqual(installation.is_public, True)

    def test_installation_mismatch(self):
        """Node and room referenced in a NodeInstallation must pertain to the same owner."""
        with self.assertRaises(ValidationError):
            RoomNodeInstallation.objects.create(
                description="An impossible installation",
                from_timestamp_s=1577836800,
                to_timestamp_s=2147483647,
                node=self.test_data["node1"],
                room=self.test_data["room2"],
            )

from uuid import UUID

from django.contrib.auth.models import User

from core.models import (
    Organization,
    Quantity,
    NodeProtocol,
    NodeModel,
    Node,
    Address,
    Site,
    Room,
)


def setup_test_auth():
    user = User.objects.create(
        username="testUser",
        email="test@test.com",
        password="password",
        first_name="Test",
        last_name="User",
        is_superuser=False,
        is_active=True,
    )
    organization = Organization.objects.create(
        name="Testorganization",
        description="This is an organization for testing only",
    )
    organization.users.add(user)
    return {"user": user, "organization": organization}


def setup_test_device(organization):
    quantities = {
        "co2": Quantity.objects.create(quantity="CO2", base_unit="PPM"),
        "temp": Quantity.objects.create(quantity="Temperature", base_unit="°C"),
        "rel_hum": Quantity.objects.create(quantity="Relative Humidity", base_unit="%"),
    }
    protocol = NodeProtocol.objects.create(
        identifier="TEST_PROTOCOL_V1", num_uplink_msgs=1, num_downlink_msgs=0
    )
    model = NodeModel.objects.create(
        name="Test Node I",
        trade_name="Testy",
        manufacturer="Test Manufacturer",
        sensor_type="Test Sensor",
    )
    for quantity in quantities.values():
        model.quantities.add(quantity)

    # Use a testing DeviceEUI. See https://lora-developers.semtech.com/library/tech-papers-and-guides/the-book/deveui/
    node = Node.objects.create(
        id=UUID(hex="0094826d4b122b94d16caf86a16f9cc3"),
        eui64="fefffffffdff0000",
        alias="Test-Node",
        protocol=protocol,
        model=model,
        owner=organization,
    )
    return {
        "quantities": quantities,
        "protocol": protocol,
        "model": model,
        "node": node,
    }


def setup_test_location(organization):
    address = Address.objects.create(
        street1="Testweg 10", zip="01234", city="Teststadt"
    )
    site = Site.objects.create(
        name="Test-Ort",
        description="Nur zum Test",
        address=address,
        operated_by=organization,
    )
    room = Room.objects.create(
        name="Test-Raum",
        description="Nur zum Test",
        size_sqm=100,
        height_m=3,
        max_occupancy=10,
        site=site,
    )
    return {"address": address, "site": site, "room": room}


def setup_basic_test_data():
    test_data = setup_test_auth()
    test_data.update(setup_test_device(test_data["organization"]))
    test_data.update(setup_test_location(test_data["organization"]))
    return test_data

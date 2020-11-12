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
    user1 = User.objects.create(
        username="testUser",
        email="test@test.com",
        password="password",
        first_name="Test",
        last_name="User",
        is_superuser=False,
        is_active=True,
    )
    user2 = User.objects.create(
        username="versuchsUser",
        email="versuch@user.com",
        password="password",
        first_name="Versuch",
        last_name="User",
        is_superuser=False,
        is_active=True,
    )
    organization1 = Organization.objects.create(
        name="Testorganization 1",
        description="This is an organization for testing only",
    )
    organization2 = Organization.objects.create(
        name="Testorganization 2",
        description="This is another organization for testing only",
    )
    organization1.users.add(user1)
    organization2.users.add(user2)
    return {
        "user1": user1,
        "user2": user2,
        "organization1": organization1,
        "organization2": organization2,
    }


def setup_test_devices(organization1, organization2):
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
    node1 = Node.objects.create(
        id=UUID(hex="0094826d4b122b94d16caf86a16f9cc3"),
        eui64="fefffffffdff0000",
        alias="Test-Node 1",
        protocol=protocol,
        model=model,
        owner=organization1,
    )
    node2 = Node.objects.create(
        id=UUID(hex="08958020b92210ddaf1f810fef43a9ed"),
        eui64="fefffffffdff0001",
        alias="Test-Node 2",
        protocol=protocol,
        model=model,
        owner=organization2,
    )
    return {
        "quantities": quantities,
        "protocol": protocol,
        "model": model,
        "node1": node1,
        "node2": node2,
    }


def setup_test_locations(organization1, organization2):
    address = Address.objects.create(
        street1="Testweg 10", zip="01234", city="Teststadt"
    )
    site1 = Site.objects.create(
        name="Test-Ort 1",
        description="Nur zum Test",
        address=address,
        operator=organization1,
    )
    site2 = Site.objects.create(
        name="Test-Ort 2",
        description="Auch zum Test",
        address=address,
        operator=organization2,
    )
    room1 = Room.objects.create(
        name="Test-Raum",
        description="Nur zum Test",
        size_sqm=100,
        height_m=3,
        max_occupancy=10,
        site=site1,
    )
    room2 = Room.objects.create(
        name="Test-Raum 2",
        description="Auch zum Test",
        size_sqm=200,
        height_m=4,
        max_occupancy=20,
        site=site2,
    )
    return {
        "address": address,
        "site1": site1,
        "room1": room1,
        "site2": site2,
        "room2": room2,
    }


def setup_basic_test_data():
    test_data = setup_test_auth()
    test_data.update(
        setup_test_devices(test_data["organization1"], test_data["organization2"])
    )
    test_data.update(
        setup_test_locations(test_data["organization1"], test_data["organization2"])
    )
    return test_data

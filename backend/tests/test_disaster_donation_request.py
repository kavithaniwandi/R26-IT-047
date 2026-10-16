from app.models.disaster_donation_request import RequestItem


def test_needed_quantity_rounds_fractional_requirement_up():
    item = RequestItem(
        itemName="First Aid Kits",
        unit="kits",
        neededQuantity=3.4000000000000004,
    )

    assert item.neededQuantity == 4


def test_needed_quantity_keeps_whole_requirement_unchanged():
    item = RequestItem(
        itemName="Blankets",
        unit="blankets",
        neededQuantity=38,
    )

    assert item.neededQuantity == 38

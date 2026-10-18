import pytest
from unittest.mock import Mock
from ..order_tracker import OrderTracker

# --- Fixtures for Unit Tests ---

@pytest.fixture
def mock_storage():
    """
    Provides a mock storage object for tests.
    This mock will be configured to simulate various storage behaviors.
    """
    mock = Mock()
    # By default, mock get_order to return None (no order found)
    mock.get_order.return_value = None
    # By default, mock get_all_orders to return an empty dict
    mock.get_all_orders.return_value = {}
    return mock

@pytest.fixture
def order_tracker(mock_storage):
    """
    Provides an OrderTracker instance initialized with the mock_storage.
    """
    return OrderTracker(mock_storage)

#
# --- Tests ---
#

# Cycle 1 & 2: add_order

def test_add_order_successfully(order_tracker, mock_storage):
    """Tests adding a new order with default 'pending' status."""
    returned = order_tracker.add_order("ORD001", "Laptop", 1, "CUST001")

    expected = {
        "order_id": "ORD001",
        "item_name": "Laptop",
        "quantity": 1,
        "customer_id": "CUST001",
        "status": "pending",
    }

    # We expect save_order to be called once, with every field stored correctly
    mock_storage.save_order.assert_called_once()
    order_id, order = mock_storage.save_order.call_args[0]
    assert order_id == "ORD001"
    assert order == expected
    # The returned order matches what was saved
    assert returned == expected


def test_add_order_raises_error_if_exists(order_tracker, mock_storage):
    """Tests that adding an order with a duplicate ID raises a ValueError."""
    # Simulate that the storage finds an existing order
    mock_storage.get_order.return_value = {"order_id": "ORD_EXISTING"}

    with pytest.raises(ValueError, match="Order with ID 'ORD_EXISTING' already exists."):
        order_tracker.add_order("ORD_EXISTING", "New Item", 1, "CUST001")
    mock_storage.save_order.assert_not_called()


# Cycle 3+: get_order_by_id

def test_get_order_by_id_existing(order_tracker, mock_storage):
    order = {"order_id": "ORD001", "status": "pending"}
    mock_storage.get_order.return_value = order

    assert order_tracker.get_order_by_id("ORD001") == order
    mock_storage.get_order.assert_called_once_with("ORD001")


def test_get_order_by_id_non_existent_returns_none(order_tracker):
    assert order_tracker.get_order_by_id("MISSING") is None


@pytest.mark.parametrize("bad_id", ["", None])
def test_get_order_by_id_empty_id_raises(order_tracker, mock_storage, bad_id):
    with pytest.raises(ValueError):
        order_tracker.get_order_by_id(bad_id)
    mock_storage.get_order.assert_not_called()


# update_order_status

def test_update_order_status_success(order_tracker, mock_storage):
    mock_storage.get_order.return_value = {"order_id": "ORD001", "status": "pending"}

    result = order_tracker.update_order_status("ORD001", "shipped")

    assert result["status"] == "shipped"
    mock_storage.save_order.assert_called_once_with(
        "ORD001", {"order_id": "ORD001", "status": "shipped"}
    )


def test_update_order_status_invalid_status_fails_fast(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Invalid status"):
        order_tracker.update_order_status("ORD001", "teleported")
    mock_storage.get_order.assert_not_called()
    mock_storage.save_order.assert_not_called()


def test_update_order_status_non_existent_order_raises(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order with ID 'MISSING' does not exist."):
        order_tracker.update_order_status("MISSING", "shipped")
    mock_storage.save_order.assert_not_called()


@pytest.mark.parametrize("bad_id", ["", None])
def test_update_order_status_empty_id_raises(order_tracker, mock_storage, bad_id):
    with pytest.raises(ValueError):
        order_tracker.update_order_status(bad_id, "shipped")
    mock_storage.save_order.assert_not_called()


# list_all_orders

def test_list_all_orders_empty(order_tracker):
    assert order_tracker.list_all_orders() == []


def test_list_all_orders_multiple(order_tracker, mock_storage):
    o1 = {"order_id": "A", "status": "pending"}
    o2 = {"order_id": "B", "status": "shipped"}
    mock_storage.get_all_orders.return_value = {"A": o1, "B": o2}

    result = order_tracker.list_all_orders()

    assert isinstance(result, list)
    assert len(result) == 2
    assert o1 in result and o2 in result


# list_orders_by_status

def test_list_orders_by_status_some_match(order_tracker, mock_storage):
    o1 = {"order_id": "A", "status": "pending"}
    o2 = {"order_id": "B", "status": "shipped"}
    o3 = {"order_id": "C", "status": "pending"}
    mock_storage.get_all_orders.return_value = {"A": o1, "B": o2, "C": o3}

    result = order_tracker.list_orders_by_status("pending")

    assert len(result) == 2
    assert o1 in result and o3 in result


def test_list_orders_by_status_none_match(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {"A": {"order_id": "A", "status": "pending"}}
    assert order_tracker.list_orders_by_status("shipped") == []


def test_list_orders_by_status_empty_storage(order_tracker):
    assert order_tracker.list_orders_by_status("pending") == []


@pytest.mark.parametrize("bad_status", ["", None, "teleported"])
def test_list_orders_by_status_invalid_status_raises(order_tracker, mock_storage, bad_status):
    with pytest.raises(ValueError):
        order_tracker.list_orders_by_status(bad_status)
    mock_storage.get_all_orders.assert_not_called()


# list_orders_by_customer

def test_list_orders_by_customer_matches_only_that_customer(order_tracker, mock_storage):
    o1 = {"order_id": "A", "customer_id": "C1", "status": "pending"}
    o2 = {"order_id": "B", "customer_id": "C2", "status": "pending"}
    mock_storage.get_all_orders.return_value = {"A": o1, "B": o2}

    assert order_tracker.list_orders_by_customer("C1") == [o1]


def test_list_orders_by_customer_none_match(order_tracker, mock_storage):
    mock_storage.get_all_orders.return_value = {"A": {"order_id": "A", "customer_id": "C1", "status": "pending"}}
    assert order_tracker.list_orders_by_customer("C9") == []


def test_list_orders_by_customer_combined_with_status(order_tracker, mock_storage):
    o1 = {"order_id": "A", "customer_id": "C1", "status": "pending"}
    o2 = {"order_id": "B", "customer_id": "C1", "status": "shipped"}
    o3 = {"order_id": "C", "customer_id": "C2", "status": "pending"}
    mock_storage.get_all_orders.return_value = {"A": o1, "B": o2, "C": o3}

    assert order_tracker.list_orders_by_customer("C1", status="pending") == [o1]


@pytest.mark.parametrize("bad_customer", ["", None])
def test_list_orders_by_customer_empty_id_raises(order_tracker, mock_storage, bad_customer):
    with pytest.raises(ValueError):
        order_tracker.list_orders_by_customer(bad_customer)
    mock_storage.get_all_orders.assert_not_called()


def test_list_orders_by_customer_invalid_status_raises(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Invalid status"):
        order_tracker.list_orders_by_customer("C1", status="teleported")
    mock_storage.get_all_orders.assert_not_called()


# delete_order

def test_delete_order_success(order_tracker, mock_storage):
    order = {"order_id": "ORD001", "status": "pending"}
    mock_storage.get_order.return_value = order

    assert order_tracker.delete_order("ORD001") == order
    mock_storage.delete_order.assert_called_once_with("ORD001")


def test_delete_order_non_existent_raises(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Order with ID 'MISSING' does not exist."):
        order_tracker.delete_order("MISSING")
    mock_storage.delete_order.assert_not_called()


@pytest.mark.parametrize("bad_id", ["", None])
def test_delete_order_empty_id_raises(order_tracker, mock_storage, bad_id):
    with pytest.raises(ValueError):
        order_tracker.delete_order(bad_id)
    mock_storage.delete_order.assert_not_called()

# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders.

class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """
    def __init__(self, storage):
        required_methods = ['save_order', 'get_order', 'get_all_orders', 'delete_order']
        for method in required_methods:
            if not hasattr(storage, method) or not callable(getattr(storage, method)):
                raise TypeError(f"Storage object must implement a callable '{method}' method.")
        self.storage = storage

    VALID_STATUSES = ("pending", "processing", "shipped")

    def add_order(self, order_id: str, item_name: str, quantity: int, customer_id: str, status: str = "pending"):
        if self.storage.get_order(order_id):
            raise ValueError(f"Order with ID '{order_id}' already exists.")

        order = {
            "order_id": order_id,
            "item_name": item_name,
            "quantity": quantity,
            "customer_id": customer_id,
            "status": status
        }
        self.storage.save_order(order_id, order)
        return order

    def get_order_by_id(self, order_id: str):
        self._require_id(order_id)
        return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        self._require_id(order_id)
        self._require_valid_status(new_status)

        order = self.storage.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID '{order_id}' does not exist.")

        order["status"] = new_status
        self.storage.save_order(order_id, order)
        return order

    def list_all_orders(self):
        return list(self.storage.get_all_orders().values())

    def list_orders_by_status(self, status: str):
        self._require_valid_status(status)
        return [o for o in self.list_all_orders() if o.get("status") == status]

    def list_orders_by_customer(self, customer_id: str, status: str = None):
        if not customer_id:
            raise ValueError("Customer ID cannot be empty.")
        if status is not None:
            self._require_valid_status(status)

        return [
            o for o in self.list_all_orders()
            if o.get("customer_id") == customer_id
            and (status is None or o.get("status") == status)
        ]

    def delete_order(self, order_id: str):
        self._require_id(order_id)
        order = self.storage.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID '{order_id}' does not exist.")

        self.storage.delete_order(order_id)
        return order

    def _require_id(self, order_id):
        if not order_id:
            raise ValueError("Order ID cannot be empty.")

    def _require_valid_status(self, status):
        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(self.VALID_STATUSES)}."
            )

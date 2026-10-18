# Udatracker Starter Code

This directory contains the starter code for the Udatracker project. The initial structure of directories and files is described below.

```
.
├── backend
│   ├── __init__.py
│   ├── app.py
│   ├── in_memory_storage.py
│   ├── order_tracker.py
│   ├── requirements.txt
│   └── tests
│       ├── __init__.py
│       ├── test_api.py
│       └── test_order_tracker.py
├── frontend
│   ├── css
│   │   └── style.css
│   ├── index.html
│   └── js
│       └── script.js
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── README.md
```

## Running

From this directory (`starter/`):

```bash
pip install -r backend/requirements.txt
python -m backend.app          # http://127.0.0.1:5000/
pytest                         # run all unit + API tests
```

### Docker (local development)

```bash
docker compose up --build      # http://127.0.0.1:5000/
```

The container runs Flask's development server (debug on, bound to `0.0.0.0`), and `backend/` and `frontend/` are mounted so edits reload automatically. It is meant for local use, not production. Orders are stored in memory and are lost when the server restarts.

## Reflection

- I used 409 for a duplicate order ID and 400 for bad input. With a duplicate, the request is fine, it just clashes with an order that already exists, so 409 made more sense to me.
- I validate before touching storage so a bad request can't leave a half-saved order behind.
- Mocking the storage made the OrderTracker tests easy to write. I also made the add_order test check every field, since checking only the status could miss a typo in the order dict.
- Next I'd move to a real database. OrderTracker only calls the storage methods, so the logic should barely change, but I'd have to think about errors and two people writing at once.

## API Reference

All endpoints are under `/api/orders` and exchange JSON. Valid statuses are `pending`, `processing` and `shipped`.

Every error uses the same shape, including unknown URLs (404) and wrong methods (405):

```json
{"error": "Order with ID 'NOPE' not found."}
```

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/api/orders` | 201 + order | 400 missing/invalid body, 409 duplicate ID |
| GET | `/api/orders` | 200 + list | 400 invalid status |
| GET | `/api/orders/<order_id>` | 200 + order | 404 not found |
| PUT | `/api/orders/<order_id>/status` | 200 + updated order | 400 missing/invalid status, 404 not found |
| DELETE | `/api/orders/<order_id>` | 204 (no body) | 404 not found |

`GET /api/orders` accepts optional query parameters `status` and `customer_id`. They can be combined.

### Sample curl commands

(bash / Git Bash; in PowerShell use `curl.exe` and escape the JSON quotes)

```bash
# Create an order (status defaults to "pending")
curl -X POST http://127.0.0.1:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD001", "item_name": "Laptop", "quantity": 1, "customer_id": "C123"}'

# Get one order
curl http://127.0.0.1:5000/api/orders/ORD001

# Update its status
curl -X PUT http://127.0.0.1:5000/api/orders/ORD001/status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "shipped"}'

# List all orders
curl http://127.0.0.1:5000/api/orders

# Filter by status, by customer, or both
curl "http://127.0.0.1:5000/api/orders?status=shipped"
curl "http://127.0.0.1:5000/api/orders?customer_id=C123"
curl "http://127.0.0.1:5000/api/orders?customer_id=C123&status=pending"

# Delete an order (204 No Content)
curl -X DELETE http://127.0.0.1:5000/api/orders/ORD001
```

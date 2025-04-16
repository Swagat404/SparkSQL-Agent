
# Database Schema and Contents

## Customers Table

| customer_id | name | email | country |
|-------------|------|-------|---------|
| 1 | John Smith | john@example.com | US |
| 2 | Jane Doe | jane@example.com | US |
| 3 | Michael Brown | michael@example.com | UK |
| 4 | Emily Wilson | emily@example.com | Canada |
| 5 | David Lee | david@example.com | US |
| 6 | Sarah Johnson | sarah@example.com | UK |
| 7 | Robert Garcia | robert@example.com | US |
| 8 | Jennifer Lopez | jennifer@example.com | US |
| 9 | William Chen | william@example.com | China |
| 10 | Lisa Kim | lisa@example.com | South Korea |

## Products Table

| product_id | name | category | cost_price | retail_price |
|------------|------|----------|------------|--------------|
| 1 | Laptop | Electronics | 800 | 1200 |
| 2 | Smartphone | Electronics | 400 | 800 |
| 3 | Headphones | Electronics | 50 | 150 |
| 4 | T-shirt | Clothing | 5 | 20 |
| 5 | Jeans | Clothing | 15 | 60 |
| 6 | Sneakers | Footwear | 30 | 90 |
| 7 | Coffee Maker | Home Appliances | 60 | 120 |
| 8 | Microwave | Home Appliances | 100 | 200 |
| 9 | Desk Chair | Furniture | 80 | 180 |
| 10 | Desk | Furniture | 120 | 250 |

## Orders Table

| order_id | customer_id | order_date | total_amount |
|----------|-------------|------------|--------------|
| 1 | 1 | 2023-01-15 | 1500 |
| 2 | 2 | 2023-02-20 | 900 |
| 3 | 1 | 2023-03-10 | 2500 |
| 4 | 3 | 2023-04-05 | 350 |
| 5 | 4 | 2023-05-12 | 120 |
| 6 | 5 | 2023-06-18 | 3800 |
| 7 | 6 | 2023-07-22 | 450 |
| 8 | 7 | 2023-08-30 | 1250 |
| 9 | 8 | 2023-09-14 | 6200 |
| 10 | 9 | 2023-10-05 | 780 |
| 11 | 10 | 2023-11-11 | 1900 |
| 12 | 1 | 2023-12-24 | 3400 |
| 13 | 2 | 2023-01-30 | 250 |
| 14 | 3 | 2023-02-14 | 680 |
| 15 | 4 | 2023-03-19 | 340 |

## Order Items Table

| item_id | order_id | product_id | quantity | price_per_unit |
|---------|----------|------------|----------|----------------|
| 1 | 1 | 1 | 1 | 1200 |
| 2 | 1 | 3 | 2 | 150 |
| 3 | 2 | 2 | 1 | 800 |
| 4 | 2 | 4 | 5 | 20 |
| 5 | 3 | 1 | 2 | 1200 |
| 6 | 3 | 5 | 2 | 60 |
| 7 | 4 | 3 | 1 | 150 |
| 8 | 4 | 6 | 2 | 90 |
| 9 | 5 | 4 | 3 | 20 |
| 10 | 5 | 6 | 2 | 90 |
| 11 | 6 | 1 | 3 | 1200 |
| 12 | 6 | 7 | 1 | 120 |
| 13 | 7 | 8 | 2 | 200 |
| 14 | 7 | 6 | 1 | 90 |
| 15 | 8 | 1 | 5 | 1200 |
| 16 | 9 | 2 | 1 | 800 |
| 17 | 10 | 9 | 2 | 180 |
| 18 | 10 | 10 | 1 | 250 |
| 19 | 11 | 10 | 2 | 250 |
| 20 | 11 | 7 | 3 | 120 |
| 21 | 12 | 1 | 2 | 1200 |
| 22 | 12 | 2 | 1 | 800 |
| 23 | 13 | 3 | 1 | 150 |
| 24 | 14 | 5 | 3 | 60 |
| 25 | 14 | 9 | 2 | 180 |
| 26 | 15 | 4 | 4 | 20 |
| 27 | 15 | 8 | 1 | 200 |

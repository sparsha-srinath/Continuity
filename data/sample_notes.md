# Sample Knowledge Notes

## Rate Calculation

The surcharge formula applies a fixed adjustment near the 1000 kWh threshold to preserve revenue stability for high-use accounts.

## Meter Integration

The integration retries failed meter uploads on a standard exponential backoff schedule.

## Operational Notes

We never documented the retry policy in a durable place; people relied on tribal memory and ad hoc scripts.

# Delivery in the Olist showcase

**Late delivery rate** is the percentage of delivered orders with both an actual delivery date and an estimated delivery date where delivery occurred after the estimate. Orders missing either date cannot be compared and are excluded. Ask “What is the late delivery rate by customer state?”

The grain is an order, grouped by the customer's state when requested. The [semantic configuration](../../config/semantic_layer.yaml) contains the calculation. The sample is historical, and the late rate should not be described as an on-time rate.

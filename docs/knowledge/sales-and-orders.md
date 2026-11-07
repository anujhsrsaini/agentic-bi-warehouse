# Sales and orders in the Olist showcase

The demo uses historical Brazilian e-commerce data, not current sales. Definitions are configured in [the semantic layer](../../config/semantic_layer.yaml); the answer also displays the calculation, filter and actual SQL.

- **GMV:** sum of item prices for non-canceled orders, excluding freight. An example is “What is GMV by customer state?” Its grain is order item; the supported state breakdown uses the order's customer state.
- **Delivered orders:** count of distinct order IDs with delivered status. Ask “How many orders were delivered?”
- **Average order value:** sum of item prices divided by distinct order IDs for delivered orders that have items. Ask “What is average order value?” Freight is excluded.

“Revenue” is ambiguous: GMV and customer payment value measure different things. The demo requests clarification. Its supported examples are deliberately limited; other dimensions or calculations require validation before use.

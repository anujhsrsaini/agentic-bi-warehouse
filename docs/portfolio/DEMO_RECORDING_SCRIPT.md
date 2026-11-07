# Recording script: analytics assistant showcase

This is a script for a future recording, not a claim that a video has already been made. Run the walkthrough first using the [README](../../README.md) and check every screen on the version being recorded. Keep the terminal large and readable; avoid showing credentials, private files, or client data.

## Before recording

- Install dependencies and launch `python demo.py` using the documented environment.
- Confirm the five menu examples, clarification, and blocked query work locally.
- Use the bundled historical Olist data; label it as 2016–2018 sample data.
- Keep the output and timing unedited in ways that could imply unsupported accuracy or speed claims.

## Walkthrough: approximately 2–3 minutes

| Time | On screen | Suggested narration |
| --- | --- | --- |
| 0:00–0:20 | Open the demo menu. | “I built this local portfolio demo to show how a business can ask a question about its data and inspect how the answer was calculated. This sample uses historical e-commerce data.” |
| 0:20–1:10 | Choose `1`: “What is GMV by customer state?” Show the result, definition, caveat, sources, and executed SQL. | “Here is item sales by customer state. The answer includes the definition and query, so a business owner can review what is included rather than relying on an unexplained number.” |
| 1:10–1:35 | Choose `6`: “Show revenue.” | “Revenue is ambiguous: this demo asks whether we mean item sales or payments. In a client project we would agree on the definition with the people who use the metric.” |
| 1:35–1:55 | Choose `7`: attempt `DROP TABLE orders`. | “The validator blocks this example before it reaches the database. A real deployment would also need database permissions and controls tailored to the client.” |
| 1:55–2:15 | Return to the menu or show the README and project repository. | “The guided demo supports a small, fixed set of questions and runs locally without an AI model. I can adapt the definitions, questions, and integration to a client's data and requirements.” |

Optional: choose `2` to briefly show late deliveries and explain that results use historical data. The selected metric, displayed filter, and wording should agree with the live output; do not infer causes from the breakdown.

## Screenshots and publishing checklist

- Capture a readable result with its definition and historical-data caveat.
- Capture the clarification and blocked-query messages.
- Link the actual repository and case study; add a video link only after the recording exists.
- Do not add a fictional customer, return on investment, deployment, or accuracy claim.
- See [FREELANCE_PROFILE.md](FREELANCE_PROFILE.md) for copy that can accompany the project.

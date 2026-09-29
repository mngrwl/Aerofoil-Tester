# Initial values and assumptions

This screen sits after constraints and before design-space setup. It distinguishes three things that must not be conflated:

- **Calculated values** follow from supplied inputs and a stated formula, such as weight `W = mg`.
- **Assumptions** are usable only after review. The current atmosphere value is an ISA estimate at a known altitude, marked provisional because local conditions can differ.
- **Optimizer variables** are not given a single design value. Span, taper, sweep, and twist remain unset until the engineer defines their search bounds in the future design-space step.

The backend derives only values with their necessary inputs. Its ISA density formula applies in the troposphere (0–11 km); outside that range it reports a missing value rather than extrapolating. Saved edits and accepted assumptions are stored per project.

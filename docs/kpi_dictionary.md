# KPI Dictionary

## SAIDI
System Average Interruption Duration Index.

```text
SAIDI = Customer Minutes Interrupted / Total Customers / 60
```

Unit: hours/customer.

## SAIFI
System Average Interruption Frequency Index.

```text
SAIFI = Interrupted Customers / Total Customers
```

Unit: interruptions/customer.

## CAIDI
Customer Average Interruption Duration Index.

```text
CAIDI = SAIDI / SAIFI × 60
```

Unit: minutes/interruption.

## Total Loss %
```text
Total Loss % = (Energy Injected - Energy Billed) / Energy Injected × 100
```

## Technical Loss %
Estimated physical network losses.

```text
Technical Loss % = Estimated Technical Loss / Energy Injected × 100
```

## Non-Technical Loss %
```text
Non-Technical Loss % = Total Loss % - Technical Loss %
```

## Collection Efficiency %
```text
Collection Efficiency % = Revenue Collected / Revenue Billed × 100
```

## Data Quality Score
Prototype weighted score:

```text
30% SCADA validity
30% OMS validity
25% meter read completeness
15% billing quality
```

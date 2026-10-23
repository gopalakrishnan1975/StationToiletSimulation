# Generated validation report

Version 6.0.0
Validated source fingerprint: `1754cb35d736a95bb5f5b9b7f161c9d20471c158e7ee78bd7b16ed7e014b9bad`

**40 tests passed.** Generated only after successful tests; regenerate whenever source changes.

| Test | Result |
|---|---|
| `test_csv_and_observed_queue_counts` | Passed |
| `test_invalid_records_rejected[change0]` | Passed |
| `test_invalid_records_rejected[change1]` | Passed |
| `test_invalid_records_rejected[change2]` | Passed |
| `test_invalid_records_rejected[change3]` | Passed |
| `test_duplicates_and_mixed_platforms_rejected` | Passed |
| `test_database_roundtrip_and_atomic_duplicates` | Passed |
| `test_data_api_requires_authentication` | Passed |
| `test_data_api_fails_closed_without_token` | Passed |
| `test_queue_api_validated_and_observed` | Passed |
| `test_fcfs_uses_facility_arrival_not_platform_arrival` | Passed |
| `test_return_walk_and_service_must_fit` | Passed |
| `test_single_fixture_never_overlaps` | Passed |
| `test_invalid_queue_parameters[changes0]` | Passed |
| `test_invalid_queue_parameters[changes1]` | Passed |
| `test_invalid_queue_parameters[changes2]` | Passed |
| `test_invalid_queue_parameters[changes3]` | Passed |
| `test_invalid_queue_parameters[changes4]` | Passed |
| `test_zero_demand_does_not_report_service_success` | Passed |
| `test_queue_target_cannot_hide_unmet_demand` | Passed |
| `test_price_exemptions_keep_demand` | Passed |
| `test_comparisons_follow_current_behaviour` | Passed |
| `test_zero_discount_supported` | Passed |
| `test_water_mass_balance_and_reuse_cap` | Passed |
| `test_zero_efficiency_rejected` | Passed |
| `test_additional_fare_reduces_required_existing_allocation` | Passed |
| `test_passenger_km_only_when_enabled` | Passed |
| `test_unit_cost_and_budget_balance` | Passed |
| `test_allocated_existing_fares_are_separate_from_incremental` | Passed |
| `test_free_fee_zero` | Passed |
| `test_tariff_transfer_not_social_benefit` | Passed |
| `test_water_scales` | Passed |
| `test_optimizer` | Passed |
| `test_conservation_and_reproducibility` | Passed |
| `test_no_fixtures` | Passed |
| `test_return_walk_deadline` | Passed |
| `test_equal_capacities` | Passed |
| `test_comparison` | Passed |
| `test_ui_run_and_stale_results_hidden` | Passed |
| `test_synthetic_data_can_drive_queue` | Passed |

## Validation scope

Unit and deterministic queue invariants, synthetic CSV validation, SQLite integration, HTTP authentication and calculation contracts, Streamlit render, observed-data run and stale-result protection.

No live PostgreSQL server, CRIS entitlement, real station data, field calibration, load test or production security review was exercised. The hosted Streamlit smoke test is performed separately after deployment.

## Reference scenario

20 trains/day; 1,000 boardings/train; 25% potential use; 37.5% urinal share; three blocks with 36 total fixtures. Peak comparison: 3 trains, 20 replications. Engineering uses potential daily demand.

| Layout | Completed/train | Unmet/train | Overall target |
|---|---:|---:|---|
| Central | 164.8 | 85.1 | Not met / insufficient demand |
| Distributed | 190.6 | 59.3 | Not met / insufficient demand |
| Hybrid | 186.1 | 63.8 | Not met / insufficient demand |

All values are synthetic planning outputs. See TECHNICAL_GUIDE.md and DESIGN_AUDIT.md for assumptions and limitations.

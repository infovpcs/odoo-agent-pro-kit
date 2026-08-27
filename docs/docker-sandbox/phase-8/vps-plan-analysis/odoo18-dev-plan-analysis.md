# PRD: VPCS Stock Min Alert (18)

## Module Overview
A tiny module that adds a boolean `low_stock_flag` computed field on `product.template` (true when `qty_available < reordering_min`), shown in the product list view. Depends: stock.

## Module Objectives
- Add a computed field `low_stock_flag` to the `product.template` model
- Flag when available quantity is below the minimum reorder quantity
- Display the flag in the product list view
- Minimal implementation focusing only on the core requirements

## Technical Requirements

### Model Changes
1. Add computed field `low_stock_flag` to `product.template`:
   - Type: Boolean
   - Compute method: `_compute_low_stock_flag`
   - Store: False (virtual field)
   - Dependencies: `_depends_on` includes stock module fields

2. Computed logic:
   - `low_stock_flag = product.qty_available < product.reordering_min`
   - Handle null values appropriately (treat as false if not set)

### View Changes
1. Add column for `low_stock_flag` in the product list view:
   - Label: "Low Stock"
   - Show boolean indicator (checkmark/x)
   - Optional: color coding (red for true, green for false)

2. Ensure proper visibility and accessibility

### Dependencies
- Stock module (`stock`) must be installed
- Module should be compatible with Odoo 18.0 (see `odoo_18_coding_standard` skill — Odoo 18 view/constraints/dependency patterns)
- Follow Odoo 18 coding standards

## Implementation Scope

### Must-Have Features
1. Computed field `low_stock_flag` on product.template
2. Logic: flag true when `qty_available < reordering_min`
3. Display in product list view

### Should-Have Features (optional)
1. Color coding for visual emphasis
2. Search/filter capability in the view
3. Export support for the flag

### Not-To-Do (deliberate exclusions)
1. Complex notification systems
2. Multi-level alert severity
3. Integration with other modules
4. Performance optimizations beyond basic requirements

## Testing Requirements
- Test field computation logic for various quantity scenarios
- Test edge cases (null values, equal values)
- Verify view display correctness
- Test with different product configurations

## Technical Constraints
- Odoo 18.0 compatibility
- Minimal footprint - no unnecessary dependencies
- Follow Odoo 18 coding standards
- No breaking changes to existing functionality

## Timeline Estimates
- Model implementation: 1-2 hours
- View implementation: 1 hour
- Testing and verification: 1-2 hours
- Total: 4-5 hours

## Success Criteria
1. Field `low_stock_flag` correctly computed for all products
2. Flag visible and accurate in product list view
3. Module installs without errors
4. Module compatible with stock module dependencies
5. All test cases passing
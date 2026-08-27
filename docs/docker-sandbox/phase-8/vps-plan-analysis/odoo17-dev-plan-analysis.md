# PRD: Partner Ref Tag

## Goal
Add a Char field `customer_ref_tag` on `res.partner` for free-text internal reference plus a search filter.

## Requirements

### Functional
- Add `customer_ref_tag` Char field to `res.partner`
- Enable search on `customer_ref_tag` via filter in partner list view
- Field is optional (no required constraint)

### Dependencies
- `base` module

## Design

### Data Model
```
res.partner.customer_ref_tag : Char (string, optional)
```

### Search Filter
- Add filter in partner tree view search bar
- Filter type: "Char Search" (ilike)

### Files to Create
```
vpcs_partner_ref_tag/
├── __manifest__.py
├── models/
│   └── res_partner.py
└── views/
    └── res_partner_views.xml
```

## Tasks
1. Create module skeleton with manifest (depends: base)
2. Extend res.partner with customer_ref_tag field
3. Create inherited views.xml with search filter on customer_ref_tag
4. Test: verify field appears in partner form, filter works in list view
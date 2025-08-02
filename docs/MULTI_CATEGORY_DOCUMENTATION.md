# Multi-Category Assignment System Documentation

## Overview

The multi-category assignment system allows products to be assigned to multiple WooCommerce categories instead of just one. This improves product discoverability and provides a better user experience by allowing products to appear in all relevant categories.

## Features

### 1. **Multiple Category Assignment**
- Products can be assigned to multiple categories (default limit: 2)
- Categories are intelligently selected from different main branches for better coverage
- Fully configurable limits and strategies

### 2. **Intelligent Category Matching**
- Hierarchical category structure matching your WooCommerce setup
- Rule-based matching using product attributes (gender, sport, type, etc.)
- Priority system to ensure the most relevant categories are selected

### 3. **Validation & Error Handling**
- Validates category limits before assignment
- Checks for valid/existing categories
- Clear error messages when limits are exceeded
- Comprehensive validation reports

### 4. **Backward Compatibility**
- Fully compatible with existing single-category products
- Can be disabled to revert to single-category mode
- No changes required to existing data

## Configuration

All settings are configured in `config.py` under `CATEGORY_MAPPING_SETTINGS`:

```python
CATEGORY_MAPPING_SETTINGS = {
    # Enable/disable multi-category assignment
    "enable_multi_category": True,
    
    # Maximum number of categories per product
    "max_categories_per_product": 2,
    
    # Separator for multiple categories in CSV (WooCommerce uses pipe |)
    "multi_category_separator": " | ",
    
    # Use only leaf category names (not full paths)
    "use_leaf_category_only": True,
    
    # Validate categories before assignment
    "validate_categories": True,
    
    # Strategy for selecting categories
    # - "complementary": Select from different main branches
    # - "all_matches": Select all matching categories
    "multi_category_strategy": "complementary"
}
```

## Usage

### Basic Usage

The system automatically applies multi-category assignment when enabled. Simply run the transformation as usual:

```bash
python run_transformation.py
```

### Testing

Run the test script to verify the multi-category functionality:

```bash
python test_multi_category.py
```

### Validation

Validate category assignments after transformation:

```bash
python validate_categories.py
```

## Category Structure

The system uses a hierarchical category structure matching your WooCommerce setup:

```
- Muži (Men)
  - Pánské oblečení (Men's Clothing)
    - Pánské mikiny (Men's Sweatshirts)
    - Pánské kalhoty (Men's Pants)
    - etc.
  - Pánské boty (Men's Shoes)
  - Pánské doplňky (Men's Accessories)

- Ženy (Women)
  - Dámské oblečení (Women's Clothing)
  - Dámské boty (Women's Shoes)
  - Dámské doplňky (Women's Accessories)

- Děti (Children)
  - Dětské oblečení (Children's Clothing)
  - Dětské boty (Children's Shoes)
  - Dětské doplňky (Children's Accessories)

- Sporty (Sports)
  - Fotbal (Football)
  - Tenis (Tennis)
  - Basketbal (Basketball)
  - etc.
```

## Examples

### Example 1: Men's Running T-Shirt
**Product**: "Pánské běžecké tričko Nike Dri-FIT"
**Attributes**: 
- Gender: Men's
- Type: T-shirt
- Sport: Running

**Result**:
1. Muži > Pánské oblečení > Pánská trička
2. Sporty > Běh > Běžecké oblečení

**CSV Output**: `Pánská trička | Běžecké oblečení`

Note: When `use_leaf_category_only` is True (default), only the final category name is used, not the full hierarchical path.

### Example 2: Children's Football Boots
**Product**: "Dětské fotbalové kopačky Adidas FG"
**Attributes**:
- Gender: Children's
- Type: Football boots
- Sport: Football
- Surface: FG

**Result**:
1. Sporty > Fotbal > Kopačky > Lisovky
2. Děti > Dětské boty

**CSV Output**: `Lisovky | Dětské boty`

## Customization

### Changing the Category Limit

To change the maximum number of categories per product, modify the configuration:

```python
CATEGORY_MAPPING_SETTINGS = {
    "max_categories_per_product": 3,  # Allow up to 3 categories
    # ... other settings
}
```

### Adding New Category Rules

To add new category mapping rules, edit `category_mapper.py` and add conditions to the category structure:

```python
"NewCategory": {
    "conditions": [
        {"params": {"type": ["new_type"]}},
        {"name_contains": ["keyword"]}
    ],
    "priority": 10,
    "subcategories": {
        # Add subcategories here
    }
}
```

### Switching Strategies

The system supports two strategies:

1. **Complementary** (default): Selects categories from different main branches
   - Better for diverse product coverage
   - Example: "Men's Clothing" + "Sports"

2. **All Matches**: Selects the best matching categories regardless of branch
   - Better for highly specific categorization
   - Example: "Football > Boots > FG" + "Football > Equipment"

Change the strategy in config:

```python
"multi_category_strategy": "all_matches"
```

## Troubleshooting

### Products Not Getting Multiple Categories

1. Check if multi-category is enabled in config
2. Verify the product has attributes that match multiple category rules
3. Check the category limit setting
4. Review the mapping report for details

### Validation Errors

Run the validation script to identify issues:

```bash
python validate_categories.py
```

Common issues:
- Category limit exceeded
- Invalid category paths
- Missing category definitions

### Performance Considerations

- The multi-category system has minimal performance impact
- Category matching is optimized with priority-based early returns
- Validation is performed in batch for efficiency

## Migration Guide

### Enabling Multi-Category for Existing Projects

1. Update `config.py` to enable multi-category
2. Run the transformation again
3. Validate the results
4. Import to WooCommerce

### Reverting to Single-Category

1. Set `enable_multi_category` to `False` in config
2. Re-run the transformation
3. Products will use only the primary category

## API Reference

### CategoryMapper.map_product_to_multiple_categories()

```python
def map_product_to_multiple_categories(
    product_name: str,
    product_params: Dict[str, Any],
    original_category: Optional[str] = None,
    max_categories: int = 2,
    strategy: str = "complementary"
) -> Tuple[List[str], str]
```

**Parameters:**
- `product_name`: Product name for matching
- `product_params`: Dictionary of product attributes
- `original_category`: Fallback category from source data
- `max_categories`: Maximum number of categories to assign
- `strategy`: Selection strategy ("complementary" or "all_matches")

**Returns:**
- Tuple of (list of category paths, mapping type)

## Best Practices

1. **Use Complementary Strategy** for general e-commerce sites
2. **Set Reasonable Limits** - 2-3 categories is usually optimal
3. **Validate Regularly** - Run validation after each import
4. **Monitor Performance** - Check category distribution reports
5. **Test Changes** - Use test scripts before production runs

## Support

For issues or questions:
1. Check the validation reports
2. Review the test outputs
3. Enable debug logging in transformer.py
4. Check the transformation.log file

---

*Version 1.0 - Multi-Category Assignment System*
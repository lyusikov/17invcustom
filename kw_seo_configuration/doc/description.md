# KW SEO Configuration Module for Odoo

## Overview
The `kw_seo_configuration` module enhances Odoo's website functionality by providing advanced SEO management capabilities. This module allows website administrators to create custom SEO rules based on product categories, attribute values, or both, enabling fine-grained control over SEO elements across different website pages.

## Key Features

### 1. SEO Model Management
- **Custom SEO Records**: Create and manage SEO records with customizable titles, descriptions, headers, and HTML content.
- **Targeted Application**: Apply SEO settings to specific product categories, attribute values, or the main shop page.
- **Multi-Website Support**: Configure SEO rules to apply to specific websites or all websites.

### 2. Flexible SEO Criteria Configuration
- **Configuration Settings**: Choose between three SEO criteria modes:
  - Category-based: Apply SEO rules based on product categories
  - Attribute-based: Apply SEO rules based on product attribute values
  - Both: Consider both categories and attributes when applying SEO rules

### 3. Enhanced Website Shop Pages
- **All Products Page SEO**: Apply custom SEO settings to the main shop page (/shop)
- **Category Page SEO**: Apply custom SEO settings to specific category pages
- **Pagination Support**: Automatically adjust SEO titles and descriptions for paginated results with page numbers

### 4. Dynamic SEO Elements
- **Custom Page Titles**: Override default page titles with SEO-optimized alternatives
- **Meta Descriptions**: Set custom meta descriptions for improved search engine listings
- **Custom Headers**: Display custom headers on shop pages
- **SEO Text Blocks**: Add rich HTML content to shop pages for improved SEO and user experience

### 5. URL Path Analysis
- **Intelligent Path Detection**: Automatically detects the current URL path and applies the appropriate SEO rules
- **Support for Various Page Types**: Handles homepage, blog pages, shop pages, and custom pages

## Technical Implementation

### Models
- **SEO Model (`seo.model`)**: Core model storing SEO configurations with fields for:
  - SEO title, description, header, and HTML text content
  - Related categories and attribute values
  - Website selection
  - All products page flag

- **Configuration Settings**: Extension of the standard Odoo settings to include SEO criteria selection

### Controllers
- **Extended Shop Controller**: Overrides the standard shop controller to apply custom SEO rules
- **Attribute Value Detection**: Detects selected attribute values from URL parameters
- **Fallback Mechanisms**: Provides default values when specific SEO rules are not found

### Views
- **SEO Model Views**: Tree and form views for managing SEO records
- **Configuration Settings**: Interface for selecting SEO criteria
- **Website Templates**: Modified templates for displaying custom SEO elements:
  - Title tag replacement
  - Meta description replacement
  - Custom category headers
  - SEO text placement

### Security
- **Access Rights**: Provides appropriate access rights for:
  - Authenticated users: Full CRUD operations
  - Public users: Read-only access

## Use Cases

1. **E-commerce SEO Optimization**: Create targeted SEO content for different product categories to improve search engine rankings
2. **Attribute-Based Landing Pages**: Generate SEO-optimized landing pages based on product attributes (e.g., color, size, brand)
3. **Multi-Website Management**: Maintain different SEO strategies across multiple websites from a single Odoo instance
4. **Content Marketing**: Add rich HTML content to category pages for improved user engagement and SEO

## Integration Points
- Integrates with Odoo's website module
- Extends the website_sale module for e-commerce functionality
- Compatible with multi-website setups

## Technical Notes
- Module version: 17.0.0.0.5
- License: OPL-1
- Dependencies: base, website, website_sale
- Custom styling for SEO text blocks